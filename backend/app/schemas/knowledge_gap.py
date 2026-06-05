from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class KnowledgeGapCreate(BaseModel):
    question: str
    priority: str = "normal"
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class KnowledgeGapUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_user_id: Optional[int] = None
    resolution_notes: Optional[str] = None


class KnowledgeGapResponse(BaseModel):
    id: int
    bank_id: int
    question: str
    status: str
    priority: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    submitted_by_user_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
