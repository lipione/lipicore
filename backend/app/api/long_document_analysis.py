from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..api.deps import get_current_user
from ..db.session import get_session
from ..models.document import Document
from ..models.long_document_analysis import LongDocumentAnalysisJob
from ..models.user import User
from ..schemas.long_document_analysis import LongDocumentAnalysisCreate, LongDocumentAnalysisResponse
from ..services.long_document_analysis_service import (
    create_long_document_analysis_job,
    enqueue_long_document_analysis_job,
)

router = APIRouter()

PRIVILEGED_ANALYSIS_ROLES = {
    "super_admin",
    "bank_admin",
    "compliance_user",
    "compliance_officer",
    "document_reviewer",
}
BLOCKED_DOCUMENT_STATUSES = {"disabled", "archived", "superseded", "failed"}
STAFF_GLOBAL_DOCUMENT_STATUSES = {"approved", "indexed", "ready"}
STAFF_GLOBAL_VERSION_STATES = {"approved"}
STAFF_SESSION_DOCUMENT_STATUSES = {"ready", "indexed", "approved"}


def _get_visible_document(db: Session, document_id: int, current_user: User) -> Document:
    doc = db.get(Document, document_id)
    if not doc or doc.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status in BLOCKED_DOCUMENT_STATUSES or doc.version_state in BLOCKED_DOCUMENT_STATUSES:
        raise HTTPException(status_code=403, detail="Document is not available for analysis")
    if current_user.role in PRIVILEGED_ANALYSIS_ROLES:
        return doc

    if (
        doc.document_scope == "session_upload"
        and doc.uploaded_by == current_user.id
        and doc.status in STAFF_SESSION_DOCUMENT_STATUSES
    ):
        return doc

    if (
        doc.document_scope == "global_knowledge"
        and doc.status in STAFF_GLOBAL_DOCUMENT_STATUSES
        and doc.version_state in STAFF_GLOBAL_VERSION_STATES
    ):
        return doc

    raise HTTPException(status_code=403, detail="Document is not available for this user")


@router.post("", response_model=LongDocumentAnalysisResponse)
def create_analysis_job(
    data: LongDocumentAnalysisCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.bank_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a bank")

    _get_visible_document(db, data.document_id, current_user)
    try:
        job = create_long_document_analysis_job(
            db,
            bank_id=current_user.bank_id,
            requested_by=current_user.id,
            data=data,
        )
        enqueue_long_document_analysis_job(job.id, db)
        db.refresh(job)
        return job
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=List[LongDocumentAnalysisResponse])
def list_analysis_jobs(
    document_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.bank_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a bank")

    limit = max(1, min(limit, 200))
    query = (
        select(LongDocumentAnalysisJob)
        .where(LongDocumentAnalysisJob.bank_id == current_user.bank_id)
        .order_by(LongDocumentAnalysisJob.updated_at.desc())
        .limit(limit)
    )
    if current_user.role not in PRIVILEGED_ANALYSIS_ROLES:
        query = query.where(LongDocumentAnalysisJob.requested_by == current_user.id)
    if document_id is not None:
        query = query.where(LongDocumentAnalysisJob.document_id == document_id)
    return db.exec(query).all()


@router.get("/{job_id}", response_model=LongDocumentAnalysisResponse)
def get_analysis_job(
    job_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    job = db.get(LongDocumentAnalysisJob, job_id)
    if not job or job.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Long document analysis job not found")
    if current_user.role not in PRIVILEGED_ANALYSIS_ROLES and job.requested_by != current_user.id:
        raise HTTPException(status_code=404, detail="Long document analysis job not found")
    return job
