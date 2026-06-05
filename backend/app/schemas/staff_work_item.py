from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StaffWorkItemCreate(BaseModel):
    assigned_to_user_id: int
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = "normal"
    due_at: Optional[datetime] = None
    metadata_json: str = "{}"


class StaffWorkItemUpdate(BaseModel):
    assigned_to_user_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_at: Optional[datetime] = None
    metadata_json: Optional[str] = None


class StaffWorkItemResponse(BaseModel):
    id: int
    bank_id: int
    assigned_to_user_id: int
    created_by_user_id: Optional[int] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata_json: str
    created_at: datetime
    updated_at: datetime
