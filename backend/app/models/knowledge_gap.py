from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class KnowledgeGap(SQLModel, table=True):
    __tablename__ = "knowledgegap"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    question: str
    status: str = Field(default="open", index=True)
    priority: str = Field(default="normal", index=True)
    source_type: Optional[str] = Field(default=None, index=True)
    source_id: Optional[str] = None
    submitted_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    assigned_to_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
