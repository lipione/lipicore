from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class PolicyChange(SQLModel, table=True):
    __tablename__ = "policychange"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    title: str
    summary: str
    impact_summary: Optional[str] = None
    affected_departments_json: str = Field(default="[]")
    action_items_json: str = Field(default="[]")
    source_document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    status: str = Field(default="published", index=True)
    published_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    published_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyChangeAcknowledgement(SQLModel, table=True):
    __tablename__ = "policychangeacknowledgement"
    __table_args__ = (
        UniqueConstraint("policy_change_id", "user_id", name="uq_policy_change_ack_user"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    policy_change_id: int = Field(foreign_key="policychange.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    acknowledged_at: datetime = Field(default_factory=datetime.utcnow)
