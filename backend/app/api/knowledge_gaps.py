from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.knowledge_gap import KnowledgeGapCreate, KnowledgeGapResponse, KnowledgeGapUpdate
from ..services.knowledge_gap_service import create_gap, list_gaps, update_gap
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[KnowledgeGapResponse])
def read_gaps(
    scope: str = "mine",
    status: Optional[str] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_gaps(db, current_user=current_user, scope=scope, status=status)


@router.post("", response_model=KnowledgeGapResponse)
def create_knowledge_gap(
    payload: KnowledgeGapCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_gap(db, current_user=current_user, payload=payload)


@router.patch("/{gap_id}", response_model=KnowledgeGapResponse)
def update_knowledge_gap(
    gap_id: int,
    payload: KnowledgeGapUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return update_gap(db, current_user=current_user, gap_id=gap_id, payload=payload)
