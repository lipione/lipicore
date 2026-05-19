from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.messenger import (
    AnnouncementConversationCreate,
    CustomConversationCreate,
    DirectConversationCreate,
    MessengerBootstrapResponse,
    MessengerConversationResponse,
    MessengerMessageCreate,
    MessengerMessageResponse,
    MessengerUnreadCountResponse,
    MessengerUserResponse,
)
from ..services import messenger_service
from .deps import get_current_user

router = APIRouter()


@router.get("/bootstrap", response_model=MessengerBootstrapResponse)
def bootstrap_messenger(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.bootstrap(db, current_user)


@router.get("/unread-count", response_model=MessengerUnreadCountResponse)
def unread_count(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return {"unread_count": messenger_service.get_total_unread_count(db, current_user)}


@router.get("/directory", response_model=List[MessengerUserResponse])
def staff_directory(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.list_directory(db, current_user)


@router.get("/conversations", response_model=List[MessengerConversationResponse])
def list_conversations(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.list_conversations(db, current_user)


@router.post("/conversations/direct", response_model=MessengerConversationResponse)
def create_direct_conversation(
    payload: DirectConversationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.create_direct_conversation(
        db,
        current_user,
        payload.recipient_id,
    )


@router.post("/conversations/custom", response_model=MessengerConversationResponse)
def create_custom_group(
    payload: CustomConversationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.create_custom_group(
        db,
        current_user,
        payload.title,
        payload.member_ids,
    )


@router.post("/conversations/announcements", response_model=MessengerConversationResponse)
def create_announcement_channel(
    payload: AnnouncementConversationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.create_announcement_channel(db, current_user, payload.title)


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessengerMessageResponse])
def list_messages(
    conversation_id: int,
    limit: int = 100,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.list_messages(db, current_user, conversation_id, limit)


@router.post("/conversations/{conversation_id}/messages", response_model=MessengerMessageResponse)
def send_message(
    conversation_id: int,
    payload: MessengerMessageCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.send_message(db, current_user, conversation_id, payload.content)


@router.post("/conversations/{conversation_id}/read", response_model=MessengerUnreadCountResponse)
def mark_read(
    conversation_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return messenger_service.mark_conversation_read(db, current_user, conversation_id)


@router.post("/conversations/{conversation_id}/attachments", response_model=MessengerMessageResponse)
async def upload_attachment(
    conversation_id: int,
    caption: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    return await messenger_service.upload_attachment(
        db,
        current_user,
        conversation_id,
        file,
        caption,
    )


@router.get("/attachments/{attachment_id}/content")
def get_attachment_content(
    attachment_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    attachment = messenger_service.get_attachment_for_member(db, current_user, attachment_id)
    return FileResponse(
        path=attachment.stored_path,
        media_type=attachment.content_type,
        filename=attachment.original_filename,
    )
