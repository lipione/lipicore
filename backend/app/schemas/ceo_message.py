from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CeoMessageCreate(BaseModel):
    bank_id: Optional[int] = None
    title: str
    body: str
    audience_type: str = "bank"
    role: Optional[str] = None
    department: Optional[str] = None
    priority: str = "normal"
    requires_acknowledgement: bool = False
    notify: bool = True
    expires_at: Optional[datetime] = None


class CeoMessageResponse(BaseModel):
    id: int
    bank_id: int
    title: str
    body: str
    audience_type: str
    role: Optional[str] = None
    department: Optional[str] = None
    priority: str
    requires_acknowledgement: bool
    notify: bool
    published_by_user_id: Optional[int] = None
    published_at: datetime
    expires_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
