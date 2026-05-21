from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..api.deps import get_current_user
from ..db.session import get_session
from ..models.loan_support import LoanSupportCase
from ..models.user import User
from ..schemas.loan_support import CreditMemoDraftUpdate, LoanSupportCreate, LoanSupportResponse
from ..services.loan_support_service import create_loan_support_case, save_credit_memo_draft

router = APIRouter()


@router.post("", response_model=LoanSupportResponse)
def create_case(
    data: LoanSupportCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_loan_support_case(db, bank_id=current_user.bank_id, created_by=current_user.id, data=data)


@router.get("", response_model=List[LoanSupportResponse])
def list_cases(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return db.exec(
        select(LoanSupportCase)
        .where(LoanSupportCase.bank_id == current_user.bank_id)
        .order_by(LoanSupportCase.updated_at.desc())
    ).all()


@router.post("/{loan_id}/credit-memo", response_model=LoanSupportResponse)
def update_credit_memo(
    loan_id: int,
    data: CreditMemoDraftUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    record = db.get(LoanSupportCase, loan_id)
    if not record or record.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Loan support case not found")
    return save_credit_memo_draft(
        db,
        loan_id=loan_id,
        generated_by=current_user.id,
        memo_draft=data.memo_draft,
        risk_factors=data.risk_factors,
        sources=data.sources,
    )
