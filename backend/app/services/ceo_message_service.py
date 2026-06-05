from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.ceo_message import CeoMessage, CeoMessageAcknowledgement
from ..models.user import User
from ..services.feature_flag_service import is_feature_enabled, require_feature_enabled
from ..services.notification_service import create_notifications


ADMIN_ROLES = {"super_admin", "bank_admin"}
VALID_AUDIENCES = {"bank", "role", "department"}


def _resolve_bank_id(current_user: User, requested_bank_id: Optional[int]) -> int:
    if current_user.role == "super_admin":
        bank_id = requested_bank_id or current_user.bank_id
        if bank_id is None:
            raise HTTPException(status_code=400, detail="No bank selected")
        return bank_id

    if requested_bank_id is not None and requested_bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Cannot access another bank's CEO messages")
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return current_user.bank_id


def _matches_audience(message: CeoMessage, user: User) -> bool:
    if message.audience_type == "bank":
        return True
    if message.audience_type == "role":
        return bool(message.role and user.role == message.role)
    if message.audience_type == "department":
        return bool(message.department and user.department == message.department)
    return False


def _acknowledged_at(db: Session, message_id: int, user_id: int) -> datetime | None:
    ack = db.exec(
        select(CeoMessageAcknowledgement).where(
            CeoMessageAcknowledgement.message_id == message_id,
            CeoMessageAcknowledgement.user_id == user_id,
        )
    ).first()
    return ack.acknowledged_at if ack else None


def _response(db: Session, message: CeoMessage, current_user: User) -> dict:
    return {
        "id": message.id,
        "bank_id": message.bank_id,
        "title": message.title,
        "body": message.body,
        "audience_type": message.audience_type,
        "role": message.role,
        "department": message.department,
        "priority": message.priority,
        "requires_acknowledgement": message.requires_acknowledgement,
        "notify": message.notify,
        "published_by_user_id": message.published_by_user_id,
        "published_at": message.published_at,
        "expires_at": message.expires_at,
        "acknowledged_at": _acknowledged_at(db, message.id, current_user.id),
    }


def _notification_severity(priority: str) -> str:
    if priority == "urgent":
        return "urgent"
    if priority == "critical":
        return "critical"
    if priority == "important":
        return "warning"
    return "info"


def create_ceo_message(
    db: Session,
    *,
    current_user: User,
    requested_bank_id: Optional[int],
    title: str,
    body: str,
    audience_type: str,
    role: Optional[str],
    department: Optional[str],
    priority: str,
    requires_acknowledgement: bool,
    notify: bool,
    expires_at: Optional[datetime],
) -> dict:
    bank_id = _resolve_bank_id(current_user, requested_bank_id)
    require_feature_enabled(db, bank_id, "ceo_messages")
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can publish CEO messages")
    if audience_type not in VALID_AUDIENCES:
        raise HTTPException(status_code=400, detail="Invalid CEO message audience")
    if audience_type == "role" and not role:
        raise HTTPException(status_code=400, detail="Role is required")
    if audience_type == "department" and not department:
        raise HTTPException(status_code=400, detail="Department is required")

    message = CeoMessage(
        bank_id=bank_id,
        title=title.strip(),
        body=body.strip(),
        audience_type=audience_type,
        role=role if audience_type == "role" else None,
        department=department if audience_type == "department" else None,
        priority=priority,
        requires_acknowledgement=requires_acknowledgement,
        notify=notify,
        published_by_user_id=current_user.id,
        expires_at=expires_at,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    if notify and is_feature_enabled(db, bank_id, "notifications"):
        create_notifications(
            db,
            current_user=current_user,
            requested_bank_id=bank_id,
            title=message.title,
            body=message.body,
            category="ceo_message",
            severity=_notification_severity(priority),
            audience_type=audience_type,
            role=message.role,
            department=message.department,
            recipient_user_ids=[],
            source_type="ceo_message",
            source_id=str(message.id),
            action_url="/ceo-messages",
            requires_acknowledgement=requires_acknowledgement,
            expires_at=expires_at,
        )
    return _response(db, message, current_user)


def list_ceo_messages(db: Session, *, current_user: User, include_expired: bool = False) -> list[dict]:
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    require_feature_enabled(db, current_user.bank_id, "ceo_messages")
    messages = db.exec(
        select(CeoMessage)
        .where(CeoMessage.bank_id == current_user.bank_id)
        .order_by(CeoMessage.published_at.desc(), CeoMessage.id.desc())
    ).all()
    now = datetime.utcnow()
    visible = []
    for message in messages:
        if not include_expired and message.expires_at and message.expires_at < now:
            continue
        if _matches_audience(message, current_user):
            visible.append(_response(db, message, current_user))
    return visible


def acknowledge_ceo_message(db: Session, *, current_user: User, message_id: int) -> dict:
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    require_feature_enabled(db, current_user.bank_id, "ceo_messages")
    message = db.get(CeoMessage, message_id)
    if not message or message.bank_id != current_user.bank_id or not _matches_audience(message, current_user):
        raise HTTPException(status_code=404, detail="CEO message not found")

    ack = db.exec(
        select(CeoMessageAcknowledgement).where(
            CeoMessageAcknowledgement.message_id == message_id,
            CeoMessageAcknowledgement.user_id == current_user.id,
        )
    ).first()
    if not ack:
        ack = CeoMessageAcknowledgement(
            bank_id=current_user.bank_id,
            message_id=message_id,
            user_id=current_user.id,
        )
        db.add(ack)
        db.commit()
        db.refresh(ack)
    return _response(db, message, current_user)
