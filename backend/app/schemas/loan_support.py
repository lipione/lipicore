from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LoanSupportCreate(BaseModel):
    applicant_name: str
    loan_type: str
    requested_amount: Optional[float] = None
    required_documents: list[str] = []
    received_documents: list[str] = []
    assigned_to: Optional[int] = None


class CreditMemoDraftUpdate(BaseModel):
    memo_draft: str
    risk_factors: list[str] = []
    sources: list[dict] = []


class LoanSupportResponse(BaseModel):
    id: int
    bank_id: int
    created_by: int
    assigned_to: Optional[int] = None
    applicant_name: str
    loan_type: str
    requested_amount: Optional[float] = None
    status: str
    required_documents_json: str
    received_documents_json: str
    missing_documents_json: str
    risk_factors_json: str
    source_document_ids_json: str
    credit_memo_draft: Optional[str] = None
    human_review_required: bool
    automated_decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
