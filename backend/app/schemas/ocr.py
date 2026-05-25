from typing import Optional

from pydantic import BaseModel


class OcrPageResponse(BaseModel):
    index: int
    label: str
    page_number: Optional[int] = None
    text: str
    character_count: int
    extraction_confidence: Optional[float] = None
    ocr_confidence: Optional[float] = None
    table_confidence: Optional[float] = None
    vision_review: Optional[str] = None


class OcrExtractResponse(BaseModel):
    file_name: str
    file_type: str
    page_count: int
    character_count: int
    full_text: str
    vision_review_requested: bool = False
    vision_review_pages: int = 0
    warnings: list[str]
    pages: list[OcrPageResponse]
