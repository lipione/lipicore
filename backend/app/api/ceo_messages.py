from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.ceo_message import CeoMessageCreate, CeoMessageResponse
from ..services.audit_service import log_audit_event
from ..services.ceo_message_service import acknowledge_ceo_message, create_ceo_message, list_ceo_messages
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[CeoMessageResponse])
def read_ceo_messages(
    include_expired: bool = False,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_ceo_messages(db, current_user=current_user, include_expired=include_expired)


@router.post("", response_model=CeoMessageResponse)
def publish_ceo_message(
    payload: CeoMessageCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    message = create_ceo_message(
        db,
        current_user=current_user,
        requested_bank_id=payload.bank_id,
        title=payload.title,
        body=payload.body,
        audience_type=payload.audience_type,
        role=payload.role,
        department=payload.department,
        priority=payload.priority,
        requires_acknowledgement=payload.requires_acknowledgement,
        notify=payload.notify,
        expires_at=payload.expires_at,
    )
    log_audit_event(
        db=db,
        action="ceo_message_publish",
        resource_type="ceo_message",
        resource_id=str(message["id"]),
        bank_id=message["bank_id"],
        user_id=current_user.id,
        metadata={
            "title": message["title"],
            "audience_type": message["audience_type"],
            "priority": message["priority"],
        },
    )
    return message


@router.patch("/{message_id}/acknowledge", response_model=CeoMessageResponse)
def acknowledge_message(
    message_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return acknowledge_ceo_message(db, current_user=current_user, message_id=message_id)
