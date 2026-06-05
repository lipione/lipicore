from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class StaffWorkItem(SQLModel, table=True):
    __tablename__ = "staffworkitem"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    assigned_to_user_id: int = Field(foreign_key="user.id", index=True)
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    source_type: Optional[str] = Field(default=None, index=True)
    source_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = Field(default="normal", index=True)
    status: str = Field(default="open", index=True)
    due_at: Optional[datetime] = Field(default=None, index=True)
    completed_at: Optional[datetime] = None
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
