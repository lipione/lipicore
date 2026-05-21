from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ComplianceReview(SQLModel, table=True):
    __tablename__ = "compliance_review"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    created_by: int = Field(foreign_key="user.id")
    assigned_to: Optional[int] = Field(default=None, foreign_key="user.id")
    title: str
    circular_document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    status: str = Field(default="draft")
    approval_status: str = Field(default="requires_officer_review")
    affected_departments_json: str = Field(default="[]")
    impact_summary: Optional[str] = None
    obligations_json: str = Field(default="[]")
    source_document_ids_json: str = Field(default="[]")
    reviewer_notes: Optional[str] = None
    disclaimer: str = Field(default="AI output is not a regulatory guarantee. Compliance officers must review and approve final interpretation.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
