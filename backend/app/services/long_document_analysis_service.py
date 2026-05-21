from datetime import datetime
import json

from sqlmodel import Session

from ..core.config import settings
from ..db.session import engine
from ..models.document import Document
from ..models.long_document_analysis import LongDocumentAnalysisJob
from ..schemas.long_document_analysis import LongDocumentAnalysisCreate
from .ingestion_queue import get_ingestion_queue
from .ingestion_service import extract_pages
from .large_document_context_service import build_large_file_prompt
from .llm_service import call_llm_a as call_deep_model


LONG_ANALYSIS_SYSTEM_PROMPT = (
    "You are LipiCore's queued long-document analysis worker for bank staff. "
    "Use only the provided document excerpts. Cite page or section labels when available. "
    "If the excerpts do not support an answer, say what is missing. "
    "Do not make final compliance, lending, or business decisions."
)


def _now() -> datetime:
    return datetime.utcnow()


def create_long_document_analysis_job(
    db: Session,
    *,
    bank_id: int,
    requested_by: int,
    data: LongDocumentAnalysisCreate,
) -> LongDocumentAnalysisJob:
    doc = db.get(Document, data.document_id)
    if not doc or doc.bank_id != bank_id:
        raise ValueError("Document not found")

    job = LongDocumentAnalysisJob(
        bank_id=bank_id,
        document_id=data.document_id,
        requested_by=requested_by,
        session_id=data.session_id,
        analysis_type=data.analysis_type,
        prompt=data.prompt,
        status="queued",
        progress=5,
        metadata_json=json.dumps({
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "queued_reason": "long_document_analysis",
        }),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def enqueue_long_document_analysis_job(job_id: int, db: Session) -> str:
    job = db.get(LongDocumentAnalysisJob, job_id)
    if not job:
        raise ValueError("Long document analysis job not found")

    queue_job_id = f"long-analysis-{job_id}"
    job.status = "queued"
    job.progress = max(job.progress or 0, 5)
    job.updated_at = _now()
    db.add(job)
    db.commit()

    try:
        queued = get_ingestion_queue().enqueue(
            "app.services.long_document_analysis_service.process_long_document_analysis_job",
            job_id,
            job_id=queue_job_id,
            job_timeout=settings.INGESTION_JOB_TIMEOUT_SECONDS,
            result_ttl=settings.INGESTION_JOB_RESULT_TTL_SECONDS,
            failure_ttl=settings.INGESTION_JOB_FAILURE_TTL_SECONDS,
        )
    except Exception as exc:
        job.status = "failed"
        job.progress = 100
        job.error_message = f"Failed to queue long-document analysis: {exc}"
        job.updated_at = _now()
        job.completed_at = _now()
        db.add(job)
        db.commit()
        raise RuntimeError("Failed to queue long-document analysis") from exc

    return queued.id


def _set_job_state(
    db: Session,
    job: LongDocumentAnalysisJob,
    *,
    status: str,
    progress: int,
    error_message: str | None = None,
) -> None:
    job.status = status
    job.progress = progress
    job.error_message = error_message
    job.updated_at = _now()
    db.add(job)
    db.commit()


def process_long_document_analysis_job(job_id: int) -> None:
    with Session(engine) as db:
        job = db.get(LongDocumentAnalysisJob, job_id)
        if not job:
            raise ValueError(f"Long document analysis job {job_id} not found")

        doc = db.get(Document, job.document_id)
        if not doc or doc.bank_id != job.bank_id:
            _set_job_state(db, job, status="failed", progress=100, error_message="Document not found")
            return

        try:
            _set_job_state(db, job, status="processing", progress=20)
            pages = extract_pages(doc.file_path, doc.file_type)
            pages = [page for page in pages if (page.get("text") or "").strip()]
            if not pages:
                raise ValueError("No text could be extracted from this document")

            _set_job_state(db, job, status="packing_context", progress=45)
            prompt, metadata = build_large_file_prompt(
                file_name=doc.file_name,
                user_request=job.prompt,
                pages=pages,
                context_window_tokens=settings.LLM_DEEP_CONTEXT_WINDOW_TOKENS,
                output_tokens=settings.LLM_DEEP_MAX_TOKENS,
            )
            metadata.update({
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "total_pages": len(pages),
                "analysis_type": job.analysis_type,
            })

            _set_job_state(db, job, status="generating", progress=70)
            result = call_deep_model(prompt, system=LONG_ANALYSIS_SYSTEM_PROMPT)
            if not result.strip():
                raise ValueError("Model returned an empty analysis")

            job.status = "completed"
            job.progress = 100
            job.result_text = result
            job.error_message = None
            job.metadata_json = json.dumps(metadata)
            job.updated_at = _now()
            job.completed_at = _now()
            db.add(job)
            db.commit()
        except Exception as exc:
            job.status = "failed"
            job.progress = 100
            job.error_message = str(exc)
            job.updated_at = _now()
            job.completed_at = _now()
            db.add(job)
            db.commit()
