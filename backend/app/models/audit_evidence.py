from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AuditEvidencePack(SQLModel, table=True):
    __tablename__ = "auditevidencepack"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    title: str
    source_type: Optional[str] = Field(default=None, index=True)
    source_id: Optional[str] = None
    summary: Optional[str] = None
    included_items_json: str = Field(default="[]")
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
