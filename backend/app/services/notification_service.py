from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, col, select

from ..models.notification import Notification
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin"}
VALID_AUDIENCES = {"bank", "role", "department", "users"}


def _resolve_bank_id(current_user: User, requested_bank_id: Optional[int]) -> int:
    if current_user.role == "super_admin":
        bank_id = requested_bank_id or current_user.bank_id
        if bank_id is None:
            raise HTTPException(status_code=400, detail="No bank selected")
        return bank_id

    if requested_bank_id is not None and requested_bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Cannot access another bank's notifications")
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return current_user.bank_id


def _notification_response(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "bank_id": notification.bank_id,
        "recipient_user_id": notification.recipient_user_id,
        "created_by_user_id": notification.created_by_user_id,
        "title": notification.title,
        "body": notification.body,
        "category": notification.category,
        "severity": notification.severity,
        "source_type": notification.source_type,
        "source_id": notification.source_id,
        "action_url": notification.action_url,
        "requires_acknowledgement": notification.requires_acknowledgement,
        "read_at": notification.read_at,
        "acknowledged_at": notification.acknowledged_at,
        "expires_at": notification.expires_at,
        "created_at": notification.created_at,
    }


def _target_users(
    db: Session,
    *,
    bank_id: int,
    audience_type: str,
    role: Optional[str],
    department: Optional[str],
    recipient_user_ids: list[int],
) -> list[User]:
    audience_type = audience_type or "bank"
    if audience_type not in VALID_AUDIENCES:
        raise HTTPException(status_code=400, detail="Invalid notification audience")

    query = select(User).where(User.bank_id == bank_id, User.is_active == True)  # noqa: E712
    if audience_type == "role":
        if not role:
            raise HTTPException(status_code=400, detail="Role is required for role audience")
        query = query.where(User.role == role)
    elif audience_type == "department":
        if not department:
            raise HTTPException(status_code=400, detail="Department is required for department audience")
        query = query.where(User.department == department)
    elif audience_type == "users":
        if not recipient_user_ids:
            raise HTTPException(status_code=400, detail="Recipient users are required")
        query = query.where(col(User.id).in_(recipient_user_ids))

    return db.exec(query.order_by(User.id)).all()


def create_notifications(
    db: Session,
    *,
    current_user: User,
    requested_bank_id: Optional[int],
    title: str,
    body: str,
    category: str,
    severity: str,
    audience_type: str,
    role: Optional[str],
    department: Optional[str],
    recipient_user_ids: list[int],
    source_type: Optional[str],
    source_id: Optional[str],
    action_url: Optional[str],
    requires_acknowledgement: bool,
    expires_at: Optional[datetime],
) -> dict:
    bank_id = _resolve_bank_id(current_user, requested_bank_id)
    require_feature_enabled(db, bank_id, "notifications")
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can create notifications")

    users = _target_users(
        db,
        bank_id=bank_id,
        audience_type=audience_type,
        role=role,
        department=department,
        recipient_user_ids=recipient_user_ids,
    )
    notifications: list[Notification] = []
    for user in users:
        notification = Notification(
            bank_id=bank_id,
            recipient_user_id=user.id,
            created_by_user_id=current_user.id,
            title=title.strip(),
            body=body.strip(),
            category=category,
            severity=severity,
            source_type=source_type,
            source_id=source_id,
            action_url=action_url,
            requires_acknowledgement=requires_acknowledgement,
            expires_at=expires_at,
        )
        db.add(notification)
        notifications.append(notification)
    db.commit()
    for notification in notifications:
        db.refresh(notification)
    return {
        "created_count": len(notifications),
        "notifications": [_notification_response(notification) for notification in notifications],
    }


def list_notifications(
    db: Session,
    *,
    current_user: User,
    include_read: bool = True,
    limit: int = 50,
) -> list[dict]:
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    require_feature_enabled(db, current_user.bank_id, "notifications")
    clamped_limit = min(max(limit, 1), 100)
    query = (
        select(Notification)
        .where(
            Notification.bank_id == current_user.bank_id,
            Notification.recipient_user_id == current_user.id,
        )
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(clamped_limit)
    )
    if not include_read:
        query = query.where(Notification.read_at == None)  # noqa: E711
    rows = db.exec(query).all()
    return [_notification_response(row) for row in rows]


def unread_count(db: Session, *, current_user: User) -> dict:
    notifications = list_notifications(db, current_user=current_user, include_read=False, limit=100)
    return {"unread_count": len(notifications)}


def _notification_for_user(db: Session, current_user: User, notification_id: int) -> Notification:
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    require_feature_enabled(db, current_user.bank_id, "notifications")
    notification = db.get(Notification, notification_id)
    if (
        not notification
        or notification.bank_id != current_user.bank_id
        or notification.recipient_user_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


def mark_read(db: Session, *, current_user: User, notification_id: int) -> dict:
    notification = _notification_for_user(db, current_user, notification_id)
    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return _notification_response(notification)


def acknowledge(db: Session, *, current_user: User, notification_id: int) -> dict:
    notification = _notification_for_user(db, current_user, notification_id)
    now = datetime.utcnow()
    if notification.read_at is None:
        notification.read_at = now
    if notification.acknowledged_at is None:
        notification.acknowledged_at = now
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return _notification_response(notification)
