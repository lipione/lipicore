from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupportCaseCreate(BaseModel):
    customer_issue: str
    category: str
    channel: str = "branch"
    priority: str = "normal"
    assigned_to: Optional[int] = None
    escalation_target: Optional[str] = None


class SupportCaseDraftUpdate(BaseModel):
    draft_response: str
    sources: list[dict] = []


class SupportCaseResponse(BaseModel):
    id: int
    bank_id: int
    created_by: int
    assigned_to: Optional[int] = None
    category: str
    channel: str
    priority: str
    customer_issue: str
    status: str
    draft_response: Optional[str] = None
    escalation_target: Optional[str] = None
    staff_review_required: bool
    source_document_ids_json: str
    answer_metadata_json: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
