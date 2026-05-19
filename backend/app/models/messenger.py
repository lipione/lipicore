from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class MessengerPolicy(SQLModel, table=True):
    __tablename__ = "messenger_policy"
    __table_args__ = (
        UniqueConstraint("bank_id", name="uq_messenger_policy_bank_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    enabled: bool = Field(default=True)
    allow_staff_groups: bool = Field(default=True)
    allow_cross_department_groups: bool = Field(default=True)
    allow_web_downloads: bool = Field(default=True)
    max_group_members: int = Field(default=50)
    max_file_size_mb: int = Field(default=25)
    allowed_file_types_json: str = Field(default='["pdf","docx","xlsx","xls","png","jpg","jpeg","txt"]')
    retention_days: int = Field(default=365)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MessengerConversation(SQLModel, table=True):
    __tablename__ = "messenger_conversation"
    __table_args__ = (
        UniqueConstraint("bank_id", "type", "direct_key", name="uq_messenger_direct_key"),
        UniqueConstraint("bank_id", "type", "department", name="uq_messenger_department"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    type: str = Field(index=True)  # direct, department, custom, announcement
    title: str
    department: Optional[str] = Field(default=None, index=True)
    direct_key: Optional[str] = Field(default=None, index=True)
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MessengerMembership(SQLModel, table=True):
    __tablename__ = "messenger_membership"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_messenger_membership_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    conversation_id: int = Field(foreign_key="messenger_conversation.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: str = Field(default="member")  # owner, admin, member, readonly
    source: str = Field(default="manual")  # direct, department, manual, system
    last_read_message_id: Optional[int] = Field(default=None, index=True)
    last_read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessengerMessage(SQLModel, table=True):
    __tablename__ = "messenger_message"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    conversation_id: int = Field(foreign_key="messenger_conversation.id", index=True)
    sender_id: int = Field(foreign_key="user.id", index=True)
    content: str
    status: str = Field(default="sent")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    deleted_at: Optional[datetime] = None


class MessengerAttachment(SQLModel, table=True):
    __tablename__ = "messenger_attachment"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    conversation_id: int = Field(foreign_key="messenger_conversation.id", index=True)
    message_id: int = Field(foreign_key="messenger_message.id", index=True)
    uploaded_by: int = Field(foreign_key="user.id", index=True)
    original_filename: str
    stored_filename: str
    stored_path: str
    content_type: str
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None


class MessengerAuditEvent(SQLModel, table=True):
    __tablename__ = "messenger_audit_event"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(index=True)
    resource_type: str
    resource_id: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

