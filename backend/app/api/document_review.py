from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..api.deps import get_current_user
from ..db.session import get_session
from ..models.document_intelligence import DocumentExtractionPage
from ..models.user import User
from ..schemas.document_intelligence import (
    DocumentExtractionPageCreate,
    DocumentExtractionPageResponse,
    DocumentExtractionReviewUpdate,
)
from ..services.document_intelligence_service import (
    create_extraction_page,
    low_confidence_queue,
    mark_extraction_reviewed,
)

router = APIRouter()


@router.get("/queue", response_model=List[DocumentExtractionPageResponse])
def read_low_confidence_queue(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return low_confidence_queue(db, bank_id=current_user.bank_id)


@router.post("/documents/{document_id}/pages", response_model=DocumentExtractionPageResponse)
def create_page_record(
    document_id: int,
    data: DocumentExtractionPageCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_extraction_page(db, bank_id=current_user.bank_id, document_id=document_id, data=data)


@router.patch("/pages/{page_id}/review", response_model=DocumentExtractionPageResponse)
def review_page(
    page_id: int,
    data: DocumentExtractionReviewUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    record = db.get(DocumentExtractionPage, page_id)
    if not record or record.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Extraction page not found")
    return mark_extraction_reviewed(
        db,
        page_id=page_id,
        reviewed_by=current_user.id,
        review_status=data.review_status,
        corrected_text=data.corrected_text,
    )
