from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    bank_id: Optional[int] = None
    title: str
    body: str
    category: str = "system"
    severity: str = "info"
    audience_type: str = "bank"
    role: Optional[str] = None
    department: Optional[str] = None
    recipient_user_ids: list[int] = []
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    requires_acknowledgement: bool = False
    expires_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    id: int
    bank_id: int
    recipient_user_id: int
    created_by_user_id: Optional[int] = None
    title: str
    body: str
    category: str
    severity: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    requires_acknowledgement: bool
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class NotificationCreateResult(BaseModel):
    created_count: int
    notifications: list[NotificationResponse]


class NotificationUnreadCount(BaseModel):
    unread_count: int
