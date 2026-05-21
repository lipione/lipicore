import json
from datetime import datetime

from sqlmodel import Session, select

from ..models.document_intelligence import DocumentExtractionPage
from ..schemas.document_intelligence import DocumentExtractionPageCreate


LOW_CONFIDENCE_THRESHOLD = 0.75


def build_extraction_flags(
    *,
    ocr_confidence: float | None = None,
    table_confidence: float | None = None,
    layout_confidence: float | None = None,
    has_handwriting: bool = False,
    has_signature_like_region: bool = False,
    has_stamp_like_region: bool = False,
    threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> list[str]:
    flags: list[str] = []
    if ocr_confidence is not None and ocr_confidence < threshold:
        flags.append("low_ocr_confidence")
    if table_confidence is not None and table_confidence < threshold:
        flags.append("low_table_confidence")
    if layout_confidence is not None and layout_confidence < threshold:
        flags.append("low_layout_confidence")
    if has_handwriting:
        flags.append("handwriting_detected")
    if has_signature_like_region:
        flags.append("signature_like_region")
    if has_stamp_like_region:
        flags.append("stamp_like_region")
    return flags


def create_extraction_page(
    db: Session,
    *,
    bank_id: int,
    document_id: int,
    data: DocumentExtractionPageCreate,
) -> DocumentExtractionPage:
    flags = build_extraction_flags(
        ocr_confidence=data.ocr_confidence,
        table_confidence=data.table_confidence,
        layout_confidence=data.layout_confidence,
        has_handwriting=data.has_handwriting,
        has_signature_like_region=data.has_signature_like_region,
        has_stamp_like_region=data.has_stamp_like_region,
    )
    record = DocumentExtractionPage(
        bank_id=bank_id,
        document_id=document_id,
        page_number=data.page_number,
        extracted_text=data.extracted_text,
        parser=data.parser,
        ocr_confidence=data.ocr_confidence,
        table_confidence=data.table_confidence,
        layout_confidence=data.layout_confidence,
        page_image_path=data.page_image_path,
        bbox_json=data.bbox_json,
        flags_json=json.dumps(flags),
        review_status="pending",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def low_confidence_queue(
    db: Session,
    *,
    bank_id: int,
    threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> list[DocumentExtractionPage]:
    rows = db.exec(
        select(DocumentExtractionPage)
        .where(DocumentExtractionPage.bank_id == bank_id)
        .where(DocumentExtractionPage.review_status == "pending")
        .order_by(DocumentExtractionPage.created_at)
    ).all()
    queued = []
    for row in rows:
        flags = json.loads(row.flags_json or "[]")
        has_low_confidence = any(
            value is not None and value < threshold
            for value in (row.ocr_confidence, row.table_confidence, row.layout_confidence)
        )
        if flags or has_low_confidence:
            queued.append(row)
    return queued


def mark_extraction_reviewed(
    db: Session,
    *,
    page_id: int,
    reviewed_by: int,
    review_status: str,
    corrected_text: str | None = None,
) -> DocumentExtractionPage:
    if review_status not in {"verified", "corrected", "unreliable"}:
        raise ValueError("Unsupported extraction review status")
    record = db.get(DocumentExtractionPage, page_id)
    if record is None:
        raise ValueError("Extraction page not found")
    record.review_status = review_status
    record.corrected_text = corrected_text
    record.reviewed_by = reviewed_by
    record.reviewed_at = datetime.utcnow()
    record.updated_at = datetime.utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
