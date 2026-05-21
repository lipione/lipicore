from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..api.deps import get_current_user
from ..db.session import get_session
from ..models.support_case import SupportCase
from ..models.user import User
from ..schemas.support_case import SupportCaseCreate, SupportCaseDraftUpdate, SupportCaseResponse
from ..services.support_case_service import create_support_case, save_support_case_draft

router = APIRouter()


@router.post("", response_model=SupportCaseResponse)
def create_case(
    data: SupportCaseCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_support_case(db, bank_id=current_user.bank_id, created_by=current_user.id, data=data)


@router.get("", response_model=List[SupportCaseResponse])
def list_cases(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return db.exec(
        select(SupportCase)
        .where(SupportCase.bank_id == current_user.bank_id)
        .order_by(SupportCase.updated_at.desc())
    ).all()


@router.post("/{case_id}/draft", response_model=SupportCaseResponse)
def update_draft(
    case_id: int,
    data: SupportCaseDraftUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    record = db.get(SupportCase, case_id)
    if not record or record.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Support case not found")
    return save_support_case_draft(
        db,
        case_id=case_id,
        generated_by=current_user.id,
        draft_response=data.draft_response,
        sources=data.sources,
    )
