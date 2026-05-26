import uuid
from typing import Iterable

from qdrant_client.models import PointStruct
from sqlmodel import Session, select

from ..core.config import settings
from ..models.bank import Bank  # noqa: F401
from ..models.chat import ChatMessage, ChatSession  # noqa: F401
from ..models.document import Document, DocumentChunk
from ..models.user import User  # noqa: F401
from .embedding_service import generate_embeddings
from .qdrant_service import delete_points_by_document, upload_points


def _chunk_payload(document: Document, chunk: DocumentChunk) -> dict:
    return {
        "bank_id": document.bank_id,
        "document_id": document.id,
        "chunk_index": chunk.chunk_index,
        "text": chunk.chunk_text,
        "page_number": chunk.page_number,
        "section_label": None,
        "extraction_confidence": chunk.extraction_confidence,
        "ocr_confidence": chunk.ocr_confidence,
        "table_confidence": chunk.table_confidence,
        "page_bbox_json": chunk.page_bbox_json,
        "department": document.department,
        "access_level": document.access_level or 0,
        "document_status": document.status,
        "version_state": document.version_state,
        "document_scope": document.document_scope,
        "session_id": document.session_id,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
    }


def _batches(items: list[DocumentChunk], batch_size: int) -> Iterable[list[DocumentChunk]]:
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def reindex_document_vectors(db: Session, document_id: int, batch_size: int = 64) -> dict:
    document = db.get(Document, document_id)
    if not document:
        return {"document_id": document_id, "status": "missing", "indexed_chunks": 0}

    chunks = db.exec(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    ).all()
    if not chunks:
        return {"document_id": document_id, "status": "no_chunks", "indexed_chunks": 0}

    delete_points_by_document(document.id, document.bank_id)
    indexed_chunks = 0
    for chunk_batch in _batches(chunks, batch_size):
        embeddings = generate_embeddings([chunk.chunk_text for chunk in chunk_batch])
        points = []
        for chunk, embedding in zip(chunk_batch, embeddings):
            point_id = str(uuid.uuid4())
            chunk.qdrant_point_id = point_id
            chunk.bank_id = document.bank_id
            chunk.department = document.department
            chunk.access_level = document.access_level or 0
            chunk.document_scope = document.document_scope
            chunk.session_id = document.session_id
            chunk.document_status = document.status
            chunk.version_state = document.version_state
            db.add(chunk)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=_chunk_payload(document, chunk),
                )
            )
        upload_points(points)
        indexed_chunks += len(points)

    document.processing_progress = 100
    document.processing_message = (
        f"Reindexed {indexed_chunks} chunks with {settings.EMBEDDING_MODEL}."
    )
    db.add(document)
    db.commit()
    return {"document_id": document_id, "status": "reindexed", "indexed_chunks": indexed_chunks}


def reindex_all_document_vectors(
    db: Session,
    bank_id: int | None = None,
    document_ids: list[int] | None = None,
    batch_size: int = 64,
) -> list[dict]:
    query = select(Document).order_by(Document.id)
    if bank_id is not None:
        query = query.where(Document.bank_id == bank_id)
    if document_ids:
        query = query.where(Document.id.in_(document_ids))

    documents = db.exec(query).all()
    return [
        reindex_document_vectors(db, document.id, batch_size=batch_size)
        for document in documents
        if document.id is not None
    ]
