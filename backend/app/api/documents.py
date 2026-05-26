from typing import Any, List, Optional
from pathlib import Path
import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from sqlalchemy import or_, and_, delete as sa_delete

from ..db.session import get_session
from ..core.config import settings
from ..models.user import User
from ..models.document import Document
from ..schemas.document import DocumentResponse
from .deps import get_current_user, get_current_bank_admin
from ..services.ingestion_queue import enqueue_document_ingestion
from ..services.audit_service import log_audit_event
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.csv', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.pptx', '.ppt'}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # Match nginx client_max_body_size.


def ensure_upload_dir() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Upload a document. Just file, no metadata needed."""
    if current_user.bank_id is None:
        from ..models.bank import Bank
        default_bank = db.exec(select(Bank).where(Bank.code == "DEFAULT")).first()
        if default_bank:
            current_user.bank_id = default_bank.id
        else:
            raise HTTPException(status_code=500, detail="No bank assigned")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Supported: PDF, DOCX, TXT, CSV, JPG, PNG, XLSX, PPTX")

    ensure_upload_dir()
    safe_name = f"{current_user.bank_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Read file content asynchronously
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 50 MB limit")

    # Write to disk
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    doc = Document(
        bank_id=current_user.bank_id,
        uploaded_by=current_user.id,
        title=file.filename,
        file_name=file.filename,
        file_type=ext.lstrip("."),
        file_path=file_path,
        document_type="other",
        access_level=0,
        version="1.0",
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    log_audit_event(
        db=db,
        action="upload",
        resource_type="document",
        resource_id=str(doc.id),
        bank_id=current_user.bank_id,
        user_id=current_user.id,
        metadata={"file_name": doc.file_name}
    )

    try:
        enqueue_document_ingestion(doc.id, db)
        db.refresh(doc)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return doc

@router.get("", response_model=List[DocumentResponse])
def read_documents(
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    ids: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve documents. Users can only see documents from their bank.
    Further filtering by department/access_level can be added here.
    """
    query = select(Document).where(Document.bank_id == current_user.bank_id)
    parsed_ids = []
    if ids:
        for raw_id in ids.split(","):
            try:
                parsed_ids.append(int(raw_id.strip()))
            except ValueError:
                continue
        if parsed_ids:
            query = query.where(Document.id.in_(parsed_ids))

    library_scope = or_(Document.document_scope != "session_upload", Document.document_scope.is_(None))
    own_session_upload = and_(
        Document.document_scope == "session_upload",
        Document.uploaded_by == current_user.id,
        Document.status != "disabled",
    )

    if current_user.role == "staff_user":
        approved_library = and_(library_scope, Document.status == "approved")
        if parsed_ids:
            # Chat restores active attachment cards by id, but normal library
            # listing must not expose session uploads as bank knowledge.
            query = query.where(or_(approved_library, own_session_upload))
        else:
            query = query.where(approved_library)
    elif parsed_ids:
        query = query.where(or_(library_scope, own_session_upload))
    else:
        query = query.where(library_scope)
        
    docs = db.exec(query.offset(skip).limit(limit)).all()
    return docs

@router.get("/{document_id}/status/stream")
async def stream_document_status(
    document_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Stream real-time document processing status.
    """
    doc = db.get(Document, document_id)
    if not doc or doc.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    async def event_generator():
        last_progress = -1
        last_status = None
        
        while True:
            # Refresh doc state
            db.refresh(doc)
            
            if doc.processing_progress != last_progress or doc.status != last_status:
                last_progress = doc.processing_progress
                last_status = doc.status
                
                payload = {
                    "document_id": doc.id,
                    "status": doc.status,
                    "progress": doc.processing_progress,
                    "message": doc.processing_message or ""
                }
                yield f"data: {json.dumps(payload)}\n\n"
                
            if doc.status in ["ready", "failed", "approved", "indexed"]:
                # Force final push
                payload = {
                    "document_id": doc.id,
                    "status": doc.status,
                    "progress": doc.processing_progress,
                    "message": doc.processing_message or ""
                }
                yield f"data: {json.dumps(payload)}\n\n"
                break
                
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.patch("/{document_id}/approve", response_model=DocumentResponse)
def approve_document(
    *,
    db: Session = Depends(get_session),
    document_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Approve a document (track who approved it)."""
    doc = db.get(Document, document_id)
    if not doc or doc.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if user has permission to approve (admin or compliance)
    if current_user.role not in ['super_admin', 'bank_admin', 'compliance_user', 'document_reviewer']:
        raise HTTPException(status_code=403, detail="Not authorized to approve")

    doc.status = "approved"
    doc.version_state = "approved"
    doc.approved_at = datetime.utcnow()
    doc.approved_by = current_user.id
    db.add(doc)
    from ..models.document import DocumentChunk
    chunks = db.exec(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)).all()
    for chunk in chunks:
        chunk.department = doc.department
        chunk.access_level = doc.access_level or 0
        chunk.document_scope = doc.document_scope
        chunk.session_id = doc.session_id
        chunk.document_status = doc.status
        chunk.version_state = doc.version_state
        db.add(chunk)
    db.commit()
    db.refresh(doc)
    try:
        from ..services.qdrant_service import update_points_by_document_payload
        update_points_by_document_payload(doc.id, doc.bank_id, {
            "department": doc.department,
            "access_level": doc.access_level or 0,
            "document_status": doc.status,
            "version_state": doc.version_state,
            "document_scope": doc.document_scope,
            "session_id": doc.session_id,
        })
    except Exception:
        pass

    log_audit_event(
        db=db,
        action="approve",
        resource_type="document",
        resource_id=str(doc.id),
        bank_id=current_user.bank_id,
        user_id=current_user.id
    )

    return doc

@router.delete("/{document_id}")
def delete_document(
    *,
    db: Session = Depends(get_session),
    document_id: int,
    current_user: User = Depends(get_current_bank_admin),
) -> Any:
    from ..models.document import DocumentChunk
    from ..services.qdrant_service import delete_points_by_document

    doc = db.get(Document, document_id)
    if not doc or doc.bank_id != current_user.bank_id:
        raise HTTPException(status_code=404, detail="Document not found")

    file_name = doc.file_name
    file_path = doc.file_path
    doc_id = doc.id
    bank_id = doc.bank_id

    # Delete Qdrant vectors
    try:
        delete_points_by_document(doc_id, bank_id)
    except Exception:
        pass

    # Delete chunk records
    db.exec(sa_delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))

    # Delete physical file
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()

    log_audit_event(
        db=db,
        action="delete",
        resource_type="document",
        resource_id=str(doc_id),
        bank_id=current_user.bank_id,
        user_id=current_user.id,
        metadata={"file_name": file_name}
    )

    return {"message": "Document deleted"}
