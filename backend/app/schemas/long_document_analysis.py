from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LongDocumentAnalysisCreate(BaseModel):
    document_id: int
    prompt: str = Field(min_length=3, max_length=4000)
    analysis_type: str = "summary"
    session_id: Optional[int] = None


class LongDocumentAnalysisResponse(BaseModel):
    id: int
    bank_id: int
    document_id: int
    requested_by: int
    session_id: Optional[int] = None
    analysis_type: str
    prompt: str
    status: str
    progress: int
    result_text: Optional[str] = None
    error_message: Optional[str] = None
    metadata_json: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
