#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from sqlalchemy import delete as sa_delete
from sqlmodel import Session, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine
from app.models.bank import Bank  # noqa: F401
from app.models.chat import ChatSession  # noqa: F401
from app.models.document import Document, DocumentChunk
from app.models.document_intelligence import DocumentExtractionPage
from app.models.user import User  # noqa: F401
from app.services.ingestion_service import process_document
from app.services.qdrant_service import (
    delete_points_by_document,
    init_qdrant,
    update_points_by_document_payload,
)


PRESERVED_DOCUMENT_FIELDS = (
    "status",
    "version_state",
    "approved_at",
    "approved_by",
    "effective_from",
    "effective_to",
    "review_due_at",
    "regulator",
    "jurisdiction",
    "document_scope",
    "session_id",
    "access_level",
    "department",
    "document_type",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Re-extract document text, rebuild DB chunks, and refresh Qdrant points.",
    )
    parser.add_argument(
        "--document-id",
        dest="document_ids",
        action="append",
        required=True,
        type=int,
        help="Document id to re-extract. Repeat for multiple documents.",
    )
    parser.add_argument(
        "--keep-ready",
        action="store_true",
        help="Leave reprocessed documents in ready/draft state instead of restoring their previous status.",
    )
    return parser


def _delete_existing_index(db: Session, document: Document) -> None:
    delete_points_by_document(document.id, document.bank_id)
    db.exec(sa_delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    db.exec(
        sa_delete(DocumentExtractionPage).where(
            DocumentExtractionPage.document_id == document.id
        )
    )
    db.commit()


def _restore_document_metadata(
    db: Session,
    document_id: int,
    snapshot: dict,
    *,
    keep_ready: bool,
) -> int:
    db.expire_all()
    document = db.get(Document, document_id)
    if not document:
        return 0

    if not keep_ready:
        for field, value in snapshot.items():
            setattr(document, field, value)
    document.processing_progress = 100
    document.processing_message = "Document text was re-extracted and the search index was rebuilt."
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    for chunk in chunks:
        chunk.bank_id = document.bank_id
        chunk.department = document.department
        chunk.access_level = document.access_level or 0
        chunk.document_scope = document.document_scope
        chunk.session_id = document.session_id
        chunk.document_status = document.status
        chunk.version_state = document.version_state
        db.add(chunk)
    db.commit()

    update_points_by_document_payload(
        document.id,
        document.bank_id,
        {
            "department": document.department,
            "access_level": document.access_level or 0,
            "document_status": document.status,
            "version_state": document.version_state,
            "document_scope": document.document_scope,
            "session_id": document.session_id,
        },
    )
    return len(chunks)


def reextract_document(db: Session, document_id: int, *, keep_ready: bool = False) -> dict:
    document = db.get(Document, document_id)
    if not document:
        return {"document_id": document_id, "status": "missing", "chunks": 0}
    if document.id is None:
        return {"document_id": document_id, "status": "missing", "chunks": 0}

    snapshot = {field: getattr(document, field) for field in PRESERVED_DOCUMENT_FIELDS}
    _delete_existing_index(db, document)

    process_document(document.id)
    chunks = _restore_document_metadata(
        db,
        document.id,
        snapshot,
        keep_ready=keep_ready,
    )
    return {"document_id": document_id, "status": "reextracted", "chunks": chunks}


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    init_qdrant()
    with Session(engine) as db:
        for document_id in args.document_ids:
            result = reextract_document(db, document_id, keep_ready=args.keep_ready)
            print(
                f"document_id={result['document_id']} "
                f"status={result['status']} "
                f"chunks={result['chunks']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
