from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BankingWorkflowCase(SQLModel, table=True):
    __tablename__ = "bankingworkflowcase"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    workflow_type: str = Field(index=True)
    title: str
    prompt: str
    output_summary: str
    customer_reference: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="draft", index=True)
    priority: str = Field(default="normal", index=True)
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    assigned_to_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
