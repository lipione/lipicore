from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class LongDocumentAnalysisJob(SQLModel, table=True):
    __tablename__ = "long_document_analysis_job"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    document_id: int = Field(foreign_key="document.id")
    requested_by: int = Field(foreign_key="user.id")
    session_id: Optional[int] = Field(default=None, foreign_key="chatsession.id")
    analysis_type: str = Field(default="summary")
    prompt: str
    status: str = Field(default="queued")
    progress: int = Field(default=0)
    result_text: Optional[str] = None
    error_message: Optional[str] = None
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
