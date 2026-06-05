from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    __tablename__ = "notification"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    recipient_user_id: int = Field(foreign_key="user.id", index=True)
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    title: str
    body: str
    category: str = Field(default="system", index=True)
    severity: str = Field(default="info", index=True)
    source_type: Optional[str] = Field(default=None, index=True)
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    requires_acknowledgement: bool = Field(default=False)
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
