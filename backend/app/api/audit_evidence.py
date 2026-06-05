from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.audit_evidence import AuditEvidencePackCreate, AuditEvidencePackResponse
from ..services.audit_evidence_service import create_pack, list_packs
from .deps import get_current_user

router = APIRouter()


@router.get("/packs", response_model=list[AuditEvidencePackResponse])
def read_packs(scope: str = "mine", db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return list_packs(db, current_user=current_user, scope=scope)


@router.post("/packs", response_model=AuditEvidencePackResponse)
def create_evidence_pack(payload: AuditEvidencePackCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return create_pack(db, current_user=current_user, payload=payload)
