import json
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.policy_change import PolicyChange, PolicyChangeAcknowledgement
from ..models.staff_work_item import StaffWorkItem
from ..models.user import User
from ..services.feature_flag_service import is_feature_enabled, require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin", "compliance_officer"}


def _require_bank(user: User) -> int:
    if user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return user.bank_id


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _visible_to(change: PolicyChange, user: User) -> bool:
    departments = _json_list(change.affected_departments_json)
    return not departments or user.department in departments


def _ack_at(db: Session, change_id: int, user_id: int) -> datetime | None:
    ack = db.exec(select(PolicyChangeAcknowledgement).where(
        PolicyChangeAcknowledgement.policy_change_id == change_id,
        PolicyChangeAcknowledgement.user_id == user_id,
    )).first()
    return ack.acknowledged_at if ack else None


def _response(db: Session, change: PolicyChange, current_user: User) -> dict:
    return {
        "id": change.id,
        "bank_id": change.bank_id,
        "title": change.title,
        "summary": change.summary,
        "impact_summary": change.impact_summary,
        "affected_departments": _json_list(change.affected_departments_json),
        "action_items": _json_list(change.action_items_json),
        "source_document_id": change.source_document_id,
        "status": change.status,
        "published_by_user_id": change.published_by_user_id,
        "published_at": change.published_at,
        "acknowledged_at": _ack_at(db, change.id, current_user.id),
    }


def create_policy_change(db: Session, *, current_user: User, payload) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "policy_changes")
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can publish policy changes")
    change = PolicyChange(
        bank_id=bank_id,
        title=payload.title.strip(),
        summary=payload.summary.strip(),
        impact_summary=payload.impact_summary,
        affected_departments_json=json.dumps(payload.affected_departments),
        action_items_json=json.dumps(payload.action_items),
        source_document_id=payload.source_document_id,
        published_by_user_id=current_user.id,
    )
    db.add(change)
    db.commit()
    db.refresh(change)
    if payload.create_work_items and is_feature_enabled(db, bank_id, "staff_inbox"):
        users = db.exec(select(User).where(User.bank_id == bank_id, User.is_active == True)).all()  # noqa: E712
        for user in users:
            if _visible_to(change, user):
                db.add(StaffWorkItem(
                    bank_id=bank_id,
                    assigned_to_user_id=user.id,
                    created_by_user_id=current_user.id,
                    source_type="policy_change",
                    source_id=str(change.id),
                    title=f"Review policy change: {change.title}",
                    description=change.impact_summary or change.summary,
                    priority="high",
                ))
        db.commit()
    return _response(db, change, current_user)


def list_policy_changes(db: Session, *, current_user: User) -> list[dict]:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "policy_changes")
    changes = db.exec(
        select(PolicyChange)
        .where(PolicyChange.bank_id == bank_id, PolicyChange.status != "archived")
        .order_by(PolicyChange.published_at.desc(), PolicyChange.id.desc())
    ).all()
    return [_response(db, change, current_user) for change in changes if _visible_to(change, current_user)]


def acknowledge_policy_change(db: Session, *, current_user: User, change_id: int) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "policy_changes")
    change = db.get(PolicyChange, change_id)
    if not change or change.bank_id != bank_id or not _visible_to(change, current_user):
        raise HTTPException(status_code=404, detail="Policy change not found")
    ack = db.exec(select(PolicyChangeAcknowledgement).where(
        PolicyChangeAcknowledgement.policy_change_id == change_id,
        PolicyChangeAcknowledgement.user_id == current_user.id,
    )).first()
    if not ack:
        ack = PolicyChangeAcknowledgement(bank_id=bank_id, policy_change_id=change_id, user_id=current_user.id)
        db.add(ack)
        db.commit()
        db.refresh(ack)
    return _response(db, change, current_user)
