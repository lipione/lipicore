from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PolicyChangeCreate(BaseModel):
    title: str
    summary: str
    impact_summary: Optional[str] = None
    affected_departments: list[str] = []
    action_items: list[str] = []
    source_document_id: Optional[int] = None
    create_work_items: bool = False


class PolicyChangeUpdate(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    impact_summary: Optional[str] = None
    affected_departments: Optional[list[str]] = None
    action_items: Optional[list[str]] = None


class PolicyChangeResponse(BaseModel):
    id: int
    bank_id: int
    title: str
    summary: str
    impact_summary: Optional[str] = None
    affected_departments: list[str] = []
    action_items: list[str] = []
    source_document_id: Optional[int] = None
    status: str
    published_by_user_id: Optional[int] = None
    published_at: datetime
    acknowledged_at: Optional[datetime] = None
