from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class DocumentExtractionPage(SQLModel, table=True):
    __tablename__ = "document_extraction_page"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    document_id: int = Field(foreign_key="document.id")
    page_number: int
    extracted_text: str = ""
    corrected_text: Optional[str] = None
    parser: str = "unknown"
    ocr_confidence: Optional[float] = None
    table_confidence: Optional[float] = None
    layout_confidence: Optional[float] = None
    page_image_path: Optional[str] = None
    bbox_json: Optional[str] = None
    flags_json: str = Field(default="[]")
    review_status: str = Field(default="pending")  # pending, verified, corrected, unreliable
    reviewed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    reviewed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
