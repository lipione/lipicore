from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.notification import (
    NotificationCreate,
    NotificationCreateResult,
    NotificationResponse,
    NotificationUnreadCount,
)
from ..services.audit_service import log_audit_event
from ..services.notification_service import acknowledge, create_notifications, list_notifications, mark_read, unread_count
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
def read_notifications(
    include_read: bool = True,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_notifications(db, current_user=current_user, include_read=include_read, limit=limit)


@router.get("/unread-count", response_model=NotificationUnreadCount)
def read_unread_count(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return unread_count(db, current_user=current_user)


@router.post("", response_model=NotificationCreateResult)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = create_notifications(
        db,
        current_user=current_user,
        requested_bank_id=payload.bank_id,
        title=payload.title,
        body=payload.body,
        category=payload.category,
        severity=payload.severity,
        audience_type=payload.audience_type,
        role=payload.role,
        department=payload.department,
        recipient_user_ids=payload.recipient_user_ids,
        source_type=payload.source_type,
        source_id=payload.source_id,
        action_url=payload.action_url,
        requires_acknowledgement=payload.requires_acknowledgement,
        expires_at=payload.expires_at,
    )
    bank_id = result["notifications"][0]["bank_id"] if result["notifications"] else payload.bank_id
    log_audit_event(
        db=db,
        action="notification_create",
        resource_type="notification",
        resource_id=str(result["created_count"]),
        bank_id=bank_id,
        user_id=current_user.id,
        metadata={
            "title": payload.title,
            "severity": payload.severity,
            "audience_type": payload.audience_type,
            "created_count": result["created_count"],
        },
    )
    return result


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return mark_read(db, current_user=current_user, notification_id=notification_id)


@router.patch("/{notification_id}/acknowledge", response_model=NotificationResponse)
def acknowledge_notification(
    notification_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return acknowledge(db, current_user=current_user, notification_id=notification_id)
