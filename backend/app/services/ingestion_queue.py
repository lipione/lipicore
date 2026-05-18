import uuid

from sqlmodel import Session

from ..core.config import settings
from ..models.document import Document


def get_ingestion_queue():
    from redis import Redis
    from rq import Queue

    redis_conn = Redis.from_url(settings.REDIS_URL)
    return Queue(
        settings.INGESTION_QUEUE_NAME,
        connection=redis_conn,
        default_timeout=settings.INGESTION_JOB_TIMEOUT_SECONDS,
    )


def _retry_policy():
    if settings.INGESTION_MAX_RETRIES <= 0:
        return None

    from rq import Retry

    return Retry(max=settings.INGESTION_MAX_RETRIES, interval=[60, 300])


def enqueue_document_ingestion(document_id: int, db: Session) -> str:
    doc = db.get(Document, document_id)
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    job_id = f"document-{document_id}-{uuid.uuid4().hex}"
    doc.status = "queued"
    doc.processing_progress = 5
    doc.processing_message = f"Queued for processing. Job: {job_id}"
    db.add(doc)
    db.commit()

    try:
        job = get_ingestion_queue().enqueue(
            "app.services.ingestion_service.process_document",
            document_id,
            job_id=job_id,
            job_timeout=settings.INGESTION_JOB_TIMEOUT_SECONDS,
            result_ttl=settings.INGESTION_JOB_RESULT_TTL_SECONDS,
            failure_ttl=settings.INGESTION_JOB_FAILURE_TTL_SECONDS,
            retry=_retry_policy(),
        )
    except Exception as exc:
        doc.status = "failed"
        doc.processing_progress = 0
        doc.processing_message = f"Failed to queue document for processing: {exc}"
        db.add(doc)
        db.commit()
        raise RuntimeError("Failed to queue document for ingestion") from exc

    return job.id
