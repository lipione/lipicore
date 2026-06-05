import json

from sqlmodel import Session, select

from ..models.document import Document, DocumentChunk
from .policy_citation_metadata import build_citation_metadata
from .qdrant_service import update_point_payload, update_points_by_document_payload


def _citation_payload(citation: dict) -> dict:
    return {
        "pdf_page_number": citation["pdf_page_number"],
        "printed_page_number": citation["printed_page_number"],
        "document_heading": citation["document_heading"],
        "clause_number": citation["clause_number"],
        "legal_hierarchy": citation.get("legal_hierarchy"),
        "citation_confidence": citation["citation_confidence"],
        "citation_incomplete_reasons": citation["citation_incomplete_reasons"],
        "citation_metadata_backfilled": True,
    }


def backfill_document_citation_metadata(db: Session, *, document_id: int, bank_id: int) -> dict:
    document = db.get(Document, document_id)
    if not document or document.bank_id != bank_id:
        return {
            "document_id": document_id,
            "updated_chunks": 0,
            "qdrant_updated_points": 0,
            "qdrant_update_errors": [],
        }

    chunks = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id, DocumentChunk.bank_id == bank_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()

    updated = 0
    qdrant_updated = 0
    qdrant_errors: list[dict[str, str]] = []
    point_payloads: list[tuple[str, dict]] = []
    for chunk in chunks:
        citation = build_citation_metadata(
            page={
                "page_number": chunk.page_number,
                "text": chunk.chunk_text,
            },
            chunk_text=chunk.chunk_text,
            document_type=document.document_type,
        )
        chunk.printed_page_number = citation["printed_page_number"]
        chunk.document_heading = citation["document_heading"]
        chunk.clause_number = citation["clause_number"]
        chunk.citation_confidence = citation["citation_confidence"]
        chunk.citation_incomplete_reasons_json = json.dumps(citation["citation_incomplete_reasons"])
        db.add(chunk)
        updated += 1

        if chunk.qdrant_point_id:
            point_payloads.append((chunk.qdrant_point_id, _citation_payload(citation)))

    db.commit()
    for point_id, payload in point_payloads:
        try:
            update_point_payload(point_id, payload, bank_id=bank_id, document_id=document_id)
            qdrant_updated += 1
        except Exception as exc:
            qdrant_errors.append({
                "scope": "point",
                "point_id": point_id,
                "error_type": type(exc).__name__,
            })
    try:
        update_points_by_document_payload(document_id, bank_id, {"citation_metadata_backfilled": True})
    except Exception as exc:
        qdrant_errors.append({
            "scope": "document",
            "document_id": str(document_id),
            "error_type": type(exc).__name__,
        })
    return {
        "document_id": document_id,
        "updated_chunks": updated,
        "qdrant_updated_points": qdrant_updated,
        "qdrant_update_errors": qdrant_errors,
    }
