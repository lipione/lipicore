from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentExtractionPageCreate(BaseModel):
    page_number: int
    extracted_text: str = ""
    parser: str = "unknown"
    ocr_confidence: Optional[float] = None
    table_confidence: Optional[float] = None
    layout_confidence: Optional[float] = None
    page_image_path: Optional[str] = None
    bbox_json: Optional[str] = None
    has_handwriting: bool = False
    has_signature_like_region: bool = False
    has_stamp_like_region: bool = False


class DocumentExtractionReviewUpdate(BaseModel):
    review_status: str
    corrected_text: Optional[str] = None


class DocumentExtractionPageResponse(BaseModel):
    id: int
    bank_id: int
    document_id: int
    page_number: int
    extracted_text: str
    corrected_text: Optional[str] = None
    parser: str
    ocr_confidence: Optional[float] = None
    table_confidence: Optional[float] = None
    layout_confidence: Optional[float] = None
    page_image_path: Optional[str] = None
    bbox_json: Optional[str] = None
    flags_json: str
    review_status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
