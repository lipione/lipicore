from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..api.deps import get_current_user
from ..db.session import get_session
from ..models.compliance_review import ComplianceReview
from ..models.user import User
from ..schemas.compliance_review import (
    ComplianceReviewCreate,
    ComplianceReviewResponse,
    ComplianceReviewSummaryUpdate,
)
from ..services.compliance_review_service import create_compliance_review, update_compliance_review_summary

router = APIRouter()


@router.post("", response_model=ComplianceReviewResponse)
def create_review(
    data: ComplianceReviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_compliance_review(db, bank_id=current_user.bank_id, created_by=current_user.id, data=data)


@router.get("", response_model=List[ComplianceReviewResponse])
def list_reviews(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return db.exec(
        select(ComplianceReview)
        .where(ComplianceReview.bank_id == current_user.bank_id)
        .order_by(ComplianceReview.updated_at.desc())
    ).all()


@router.post("/{review_id}/summary", response_model=ComplianceReviewResponse)
def update_summary(
    review_id: int,
    data: ComplianceReviewSummaryUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    record = db.get(ComplianceReview, review_id)
    if not record or record.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Compliance review not found")
    return update_compliance_review_summary(
        db,
        review_id=review_id,
        generated_by=current_user.id,
        impact_summary=data.impact_summary,
        obligations=data.obligations,
        sources=data.sources,
    )
