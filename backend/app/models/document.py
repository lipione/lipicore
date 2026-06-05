from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .bank import Bank

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    uploaded_by: int = Field(foreign_key="user.id")
    title: str = ""
    file_name: str
    file_type: str
    file_path: str

    # Auto-cataloging (filled by LLM in background)
    document_type: str = "other"  # policy, procedure, manual, compliance, report, circular, directive, other
    department: Optional[str] = None     # Credit, Treasury, Operations, HR, Compliance, Audit, IT, Risk, General
    access_level: int = 0
    summary: Optional[str] = None

    # Status and progress
    status: str = Field(default="uploaded")  # uploaded, queued, processing, extracting_text, chunking, embedding, indexed, approved, disabled, failed
    version_state: str = Field(default="draft")  # draft, approved, superseded, archived, disabled
    version: str = "1.0"
    supersedes_document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = Field(default=None, foreign_key="user.id")
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    review_due_at: Optional[datetime] = None
    regulator: Optional[str] = None
    jurisdiction: Optional[str] = None
    superseded_reason: Optional[str] = None
    processing_progress: int = Field(default=0)
    processing_message: Optional[str] = None

    # Chat session uploads
    session_id: Optional[int] = Field(default=None, foreign_key="chatsession.id")
    document_scope: Optional[str] = Field(default="global_knowledge")  # session_upload, global_knowledge

    created_at: datetime = Field(default_factory=datetime.utcnow)

    bank: Optional["Bank"] = Relationship(back_populates="documents")
    chunks: List["DocumentChunk"] = Relationship(back_populates="document")

class DocumentChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    document_id: int = Field(foreign_key="document.id")
    chunk_index: int
    chunk_text: str
    page_number: Optional[int] = None
    printed_page_number: Optional[str] = None
    document_heading: Optional[str] = None
    clause_number: Optional[str] = None
    citation_confidence: Optional[float] = None
    citation_incomplete_reasons_json: str = "[]"
    qdrant_point_id: str
    extraction_confidence: Optional[float] = None
    ocr_confidence: Optional[float] = None
    table_confidence: Optional[float] = None
    page_bbox_json: Optional[str] = None
    source_risk_level: str = "low"
    source_risk_flags_json: str = "[]"
    department: Optional[str] = None
    access_level: int = 0
    document_scope: Optional[str] = "global_knowledge"
    session_id: Optional[int] = None
    document_status: str = "uploaded"
    version_state: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    document: Optional["Document"] = Relationship(back_populates="chunks")
