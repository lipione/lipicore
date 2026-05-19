from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    title: str
    document_type: str
    department: Optional[str] = None
    access_level: int = 0

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    bank_id: int
    uploaded_by: int
    file_name: str
    file_type: str
    status: str
    version_state: str = "draft"
    version: str
    supersedes_document_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    session_id: Optional[int] = None
    document_scope: str = "global_knowledge"
    processing_progress: int = 0
    processing_message: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True
