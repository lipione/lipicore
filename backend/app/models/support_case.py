from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SupportCase(SQLModel, table=True):
    __tablename__ = "support_case"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    created_by: int = Field(foreign_key="user.id")
    assigned_to: Optional[int] = Field(default=None, foreign_key="user.id")
    category: str
    channel: str = "branch"
    priority: str = "normal"
    customer_issue: str
    status: str = Field(default="open")
    draft_response: Optional[str] = None
    escalation_target: Optional[str] = None
    staff_review_required: bool = Field(default=True)
    source_document_ids_json: str = Field(default="[]")
    answer_metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
