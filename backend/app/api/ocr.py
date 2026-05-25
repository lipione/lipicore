import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from ..api.deps import get_current_user
from ..core.config import settings
from ..db.session import get_session
from ..models.user import User
from ..schemas.ocr import OcrExtractResponse, OcrPageResponse
from ..services.audit_service import log_audit_event
from ..services.ingestion_service import extract_pages

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".csv",
    ".jpg",
    ".jpeg",
    ".png",
    ".xlsx",
    ".xls",
    ".pptx",
    ".ppt",
}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
SHEET_LABEL_RE = re.compile(r"---\s*Sheet:\s*(.+?)\s*---", re.IGNORECASE)


def _ensure_ocr_upload_dir() -> str:
    upload_dir = os.path.join(settings.UPLOAD_DIR, "ocr_extract")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def _page_label(*, file_type: str, page: dict, index: int) -> str:
    page_number = page.get("page_number")
    if page_number:
        if file_type in {"ppt", "pptx"}:
            return f"Slide {page_number}"
        return f"Page {page_number}"
    if file_type in {"xlsx", "xls"}:
        match = SHEET_LABEL_RE.search(page.get("text") or "")
        return f"Sheet: {match.group(1).strip()}" if match else f"Sheet {index}"
    if file_type == "csv":
        return "CSV"
    if file_type == "txt":
        return "Text"
    return f"Section {index}"


def _warnings_for_pages(pages: list[dict], full_text: str) -> list[str]:
    warnings: list[str] = []
    if not full_text.strip():
        warnings.append("No extractable text was found.")
    if any((page.get("ocr_confidence") or 1.0) < 0.75 for page in pages):
        warnings.append("OCR confidence is low on one or more pages; staff review is required before high-risk use.")
    if any((page.get("table_confidence") or 1.0) < 0.75 for page in pages):
        warnings.append("Table extraction confidence is low on one or more pages.")
    return warnings


@router.post("/extract", response_model=OcrExtractResponse)
async def extract_ocr_text(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    file_name = file.filename or "uploaded-file"
    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Supported: PDF, DOCX, TXT, CSV, JPG, PNG, XLSX, XLS, PPTX, PPT",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit")

    upload_dir = _ensure_ocr_upload_dir()
    file_type = ext.lstrip(".")
    temp_path = os.path.join(upload_dir, f"{current_user.bank_id}_{uuid.uuid4().hex}{ext}")

    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(content)

        try:
            raw_pages = extract_pages(temp_path, file_type)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Text extraction failed for this file: {exc}") from exc

        pages: list[OcrPageResponse] = []
        text_parts: list[str] = []
        for index, page in enumerate(raw_pages, start=1):
            text = (page.get("text") or "").strip()
            if not text:
                continue
            text_parts.append(text)
            pages.append(
                OcrPageResponse(
                    index=index,
                    label=_page_label(file_type=file_type, page=page, index=index),
                    page_number=page.get("page_number"),
                    text=text,
                    character_count=len(text),
                    extraction_confidence=page.get("extraction_confidence"),
                    ocr_confidence=page.get("ocr_confidence"),
                    table_confidence=page.get("table_confidence"),
                )
            )

        full_text = "\n\n".join(text_parts)
        if not full_text:
            raise HTTPException(status_code=422, detail="No text could be extracted from this file")

        log_audit_event(
            db=db,
            action="ocr_extract",
            resource_type="ocr",
            resource_id=file_name,
            bank_id=current_user.bank_id,
            user_id=current_user.id,
            metadata={
                "file_name": file_name,
                "file_type": file_type,
                "file_size": len(content),
                "page_count": len(pages),
                "character_count": len(full_text),
            },
        )

        return OcrExtractResponse(
            file_name=file_name,
            file_type=file_type,
            page_count=len(pages),
            character_count=len(full_text),
            full_text=full_text,
            warnings=_warnings_for_pages(raw_pages, full_text),
            pages=pages,
        )
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
