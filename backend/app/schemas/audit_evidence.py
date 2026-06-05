from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditEvidencePackCreate(BaseModel):
    title: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    summary: Optional[str] = None
    included_items: list[str] = []


class AuditEvidencePackResponse(BaseModel):
    id: int
    bank_id: int
    title: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    summary: Optional[str] = None
    included_items: list[str] = []
    created_by_user_id: Optional[int] = None
    created_at: datetime
