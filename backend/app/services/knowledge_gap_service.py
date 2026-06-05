from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.knowledge_gap import KnowledgeGap
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin", "compliance_officer"}


def _require_bank(user: User) -> int:
    if user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return user.bank_id


def _response(gap: KnowledgeGap) -> dict:
    return {
        "id": gap.id,
        "bank_id": gap.bank_id,
        "question": gap.question,
        "status": gap.status,
        "priority": gap.priority,
        "source_type": gap.source_type,
        "source_id": gap.source_id,
        "submitted_by_user_id": gap.submitted_by_user_id,
        "assigned_to_user_id": gap.assigned_to_user_id,
        "resolution_notes": gap.resolution_notes,
        "created_at": gap.created_at,
        "updated_at": gap.updated_at,
    }


def create_gap(db: Session, *, current_user: User, payload) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "knowledge_gaps")
    gap = KnowledgeGap(
        bank_id=bank_id,
        question=payload.question.strip(),
        priority=payload.priority,
        source_type=payload.source_type,
        source_id=payload.source_id,
        submitted_by_user_id=current_user.id,
        assigned_to_user_id=payload.assigned_to_user_id,
    )
    db.add(gap)
    db.commit()
    db.refresh(gap)
    return _response(gap)


def list_gaps(db: Session, *, current_user: User, scope: str = "mine", status: str | None = None) -> list[dict]:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "knowledge_gaps")
    query = select(KnowledgeGap).where(KnowledgeGap.bank_id == bank_id)
    if scope == "bank":
        if current_user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Only admins can list bank-wide gaps")
    else:
        query = query.where(KnowledgeGap.submitted_by_user_id == current_user.id)
    if status:
        query = query.where(KnowledgeGap.status == status)
    query = query.order_by(KnowledgeGap.created_at.desc(), KnowledgeGap.id.desc())
    return [_response(gap) for gap in db.exec(query).all()]


def update_gap(db: Session, *, current_user: User, gap_id: int, payload) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "knowledge_gaps")
    gap = db.get(KnowledgeGap, gap_id)
    if not gap or gap.bank_id != bank_id:
        raise HTTPException(status_code=404, detail="Knowledge gap not found")
    if current_user.role not in ADMIN_ROLES and gap.submitted_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot update another user's knowledge gap")
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(gap, key, value)
    gap.updated_at = datetime.utcnow()
    db.add(gap)
    db.commit()
    db.refresh(gap)
    return _response(gap)
