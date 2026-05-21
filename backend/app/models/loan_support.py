from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class LoanSupportCase(SQLModel, table=True):
    __tablename__ = "loan_support_case"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    created_by: int = Field(foreign_key="user.id")
    assigned_to: Optional[int] = Field(default=None, foreign_key="user.id")
    applicant_name: str
    loan_type: str
    requested_amount: Optional[float] = None
    status: str = Field(default="draft")
    required_documents_json: str = Field(default="[]")
    received_documents_json: str = Field(default="[]")
    missing_documents_json: str = Field(default="[]")
    risk_factors_json: str = Field(default="[]")
    source_document_ids_json: str = Field(default="[]")
    credit_memo_draft: Optional[str] = None
    human_review_required: bool = Field(default=True)
    automated_decision: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
