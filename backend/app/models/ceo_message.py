from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class CeoMessage(SQLModel, table=True):
    __tablename__ = "ceomessage"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    title: str
    body: str
    audience_type: str = Field(default="bank", index=True)
    role: Optional[str] = Field(default=None, index=True)
    department: Optional[str] = Field(default=None, index=True)
    priority: str = Field(default="normal", index=True)
    requires_acknowledgement: bool = Field(default=False)
    notify: bool = Field(default=True)
    published_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    published_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CeoMessageAcknowledgement(SQLModel, table=True):
    __tablename__ = "ceomessageacknowledgement"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_ceo_message_ack_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    message_id: int = Field(foreign_key="ceomessage.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    acknowledged_at: datetime = Field(default_factory=datetime.utcnow)
