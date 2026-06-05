from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.staff_work_item import StaffWorkItem
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin"}
TERMINAL_STATUSES = {"completed", "dismissed"}


def _require_bank(current_user: User) -> int:
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return current_user.bank_id


def _response(item: StaffWorkItem) -> dict:
    return {
        "id": item.id,
        "bank_id": item.bank_id,
        "assigned_to_user_id": item.assigned_to_user_id,
        "created_by_user_id": item.created_by_user_id,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "title": item.title,
        "description": item.description,
        "priority": item.priority,
        "status": item.status,
        "due_at": item.due_at,
        "completed_at": item.completed_at,
        "metadata_json": item.metadata_json,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def create_work_item(db: Session, *, current_user: User, payload) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "staff_inbox")
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can create work items")
    assignee = db.get(User, payload.assigned_to_user_id)
    if not assignee or assignee.bank_id != bank_id:
        raise HTTPException(status_code=403, detail="Cannot assign work item outside this bank")

    item = StaffWorkItem(
        bank_id=bank_id,
        assigned_to_user_id=payload.assigned_to_user_id,
        created_by_user_id=current_user.id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        title=payload.title.strip(),
        description=payload.description,
        priority=payload.priority,
        due_at=payload.due_at,
        metadata_json=payload.metadata_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _response(item)


def list_work_items(
    db: Session,
    *,
    current_user: User,
    scope: str = "mine",
    status: Optional[str] = None,
    include_closed: bool = True,
) -> list[dict]:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "staff_inbox")
    query = select(StaffWorkItem).where(StaffWorkItem.bank_id == bank_id)
    if scope == "bank":
        if current_user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Only admins can list bank-wide work items")
    else:
        query = query.where(StaffWorkItem.assigned_to_user_id == current_user.id)
    if status:
        query = query.where(StaffWorkItem.status == status)
    elif not include_closed:
        query = query.where(StaffWorkItem.status.notin_(TERMINAL_STATUSES))
    query = query.order_by(StaffWorkItem.due_at.is_(None), StaffWorkItem.due_at, StaffWorkItem.created_at.desc())
    return [_response(item) for item in db.exec(query).all()]


def update_work_item(db: Session, *, current_user: User, item_id: int, payload) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "staff_inbox")
    item = db.get(StaffWorkItem, item_id)
    if not item or item.bank_id != bank_id:
        raise HTTPException(status_code=404, detail="Work item not found")
    if current_user.role not in ADMIN_ROLES and item.assigned_to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot update another user's work item")

    update_data = payload.dict(exclude_unset=True)
    if "assigned_to_user_id" in update_data:
        if current_user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Only admins can reassign work items")
        assignee = db.get(User, update_data["assigned_to_user_id"])
        if not assignee or assignee.bank_id != bank_id:
            raise HTTPException(status_code=403, detail="Cannot assign work item outside this bank")
    for key, value in update_data.items():
        setattr(item, key, value)
    if item.status in TERMINAL_STATUSES and item.completed_at is None:
        item.completed_at = datetime.utcnow()
    if item.status not in TERMINAL_STATUSES:
        item.completed_at = None
    item.updated_at = datetime.utcnow()
    db.add(item)
    db.commit()
    db.refresh(item)
    return _response(item)
