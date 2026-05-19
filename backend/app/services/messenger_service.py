import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from ..core.config import settings
from ..models.messenger import (
    MessengerAttachment,
    MessengerAuditEvent,
    MessengerConversation,
    MessengerMembership,
    MessengerMessage,
    MessengerPolicy,
)
from ..models.user import User

DEFAULT_ALLOWED_FILE_TYPES = ["pdf", "docx", "xlsx", "xls", "png", "jpg", "jpeg", "txt"]
ADMIN_ROLES = {"super_admin", "bank_admin"}
MANAGER_ROLES = {"super_admin", "bank_admin", "compliance_user", "document_reviewer"}


def require_bank_id(user: User) -> int:
    if user.bank_id is None:
        raise HTTPException(status_code=400, detail="User is not assigned to a bank")
    return user.bank_id


def _now() -> datetime:
    return datetime.utcnow()


def _clean_department(department: Optional[str]) -> Optional[str]:
    if not department:
        return None
    cleaned = " ".join(department.split())
    return cleaned or None


def _direct_key(user_a: int, user_b: int) -> str:
    first, second = sorted([user_a, user_b])
    return f"{first}:{second}"


def _allowed_file_types(policy: MessengerPolicy) -> List[str]:
    try:
        parsed = json.loads(policy.allowed_file_types_json)
    except json.JSONDecodeError:
        parsed = DEFAULT_ALLOWED_FILE_TYPES
    return [str(item).lower().lstrip(".") for item in parsed]


def get_or_create_policy(db: Session, bank_id: int) -> MessengerPolicy:
    policy = db.exec(
        select(MessengerPolicy).where(MessengerPolicy.bank_id == bank_id)
    ).first()
    if policy:
        return policy

    policy = MessengerPolicy(bank_id=bank_id)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def log_event(
    db: Session,
    *,
    bank_id: int,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> None:
    event = MessengerAuditEvent(
        bank_id=bank_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
    db.commit()


def _user_response(user: User) -> Dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "department": user.department,
    }


def _policy_response(policy: MessengerPolicy) -> Dict:
    return {
        "enabled": policy.enabled,
        "allow_staff_groups": policy.allow_staff_groups,
        "allow_cross_department_groups": policy.allow_cross_department_groups,
        "allow_web_downloads": policy.allow_web_downloads,
        "max_group_members": policy.max_group_members,
        "max_file_size_mb": policy.max_file_size_mb,
        "allowed_file_types": _allowed_file_types(policy),
        "retention_days": policy.retention_days,
    }


def _memberships_for_conversation(db: Session, conversation_id: int) -> List[MessengerMembership]:
    return db.exec(
        select(MessengerMembership).where(
            MessengerMembership.conversation_id == conversation_id
        )
    ).all()


def _users_by_id(db: Session, user_ids: Iterable[int]) -> Dict[int, User]:
    ids = list({user_id for user_id in user_ids if user_id is not None})
    if not ids:
        return {}
    users = db.exec(select(User).where(User.id.in_(ids))).all()
    return {user.id: user for user in users if user.id is not None}


def _attachments_for_message(db: Session, message_id: int) -> List[MessengerAttachment]:
    return db.exec(
        select(MessengerAttachment)
        .where(MessengerAttachment.message_id == message_id)
        .where(MessengerAttachment.deleted_at.is_(None))
        .order_by(MessengerAttachment.created_at)
    ).all()


def _attachment_response(attachment: MessengerAttachment) -> Dict:
    return {
        "id": attachment.id,
        "original_filename": attachment.original_filename,
        "stored_path": attachment.stored_path,
        "content_type": attachment.content_type,
        "size_bytes": attachment.size_bytes,
        "created_at": attachment.created_at,
        "download_url": f"/api/messenger/attachments/{attachment.id}/content",
    }


def _message_response(db: Session, message: MessengerMessage) -> Dict:
    sender = db.get(User, message.sender_id)
    attachments = _attachments_for_message(db, message.id)
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender": _user_response(sender) if sender else {
            "id": message.sender_id,
            "name": "Unknown user",
            "email": "",
            "role": "unknown",
            "department": None,
        },
        "content": message.content,
        "status": message.status,
        "created_at": message.created_at,
        "attachments": [_attachment_response(attachment) for attachment in attachments],
    }


def _last_message(db: Session, conversation_id: int) -> Optional[MessengerMessage]:
    return db.exec(
        select(MessengerMessage)
        .where(MessengerMessage.conversation_id == conversation_id)
        .where(MessengerMessage.deleted_at.is_(None))
        .order_by(MessengerMessage.id.desc())
    ).first()


def _unread_count_for_membership(db: Session, membership: MessengerMembership) -> int:
    query = (
        select(MessengerMessage)
        .where(MessengerMessage.conversation_id == membership.conversation_id)
        .where(MessengerMessage.sender_id != membership.user_id)
        .where(MessengerMessage.deleted_at.is_(None))
    )
    if membership.last_read_message_id is not None:
        query = query.where(MessengerMessage.id > membership.last_read_message_id)
    return len(db.exec(query).all())


def get_total_unread_count(db: Session, user: User) -> int:
    bank_id = require_bank_id(user)
    memberships = db.exec(
        select(MessengerMembership).where(
            MessengerMembership.bank_id == bank_id,
            MessengerMembership.user_id == user.id,
        )
    ).all()
    return sum(_unread_count_for_membership(db, membership) for membership in memberships)


def _conversation_title(db: Session, conversation: MessengerConversation, current_user_id: int) -> str:
    if conversation.type != "direct":
        return conversation.title

    memberships = _memberships_for_conversation(db, conversation.id)
    other_ids = [membership.user_id for membership in memberships if membership.user_id != current_user_id]
    users = _users_by_id(db, other_ids)
    if users:
        return next(iter(users.values())).name
    return conversation.title


def conversation_response(db: Session, conversation: MessengerConversation, current_user: User) -> Dict:
    memberships = _memberships_for_conversation(db, conversation.id)
    user_map = _users_by_id(db, [membership.user_id for membership in memberships])
    current_membership = next(
        (membership for membership in memberships if membership.user_id == current_user.id),
        None,
    )
    last = _last_message(db, conversation.id)
    return {
        "id": conversation.id,
        "type": conversation.type,
        "title": _conversation_title(db, conversation, current_user.id),
        "department": conversation.department,
        "role": current_membership.role if current_membership else "none",
        "members": [
            _user_response(user_map[membership.user_id])
            for membership in memberships
            if membership.user_id in user_map
        ],
        "last_message": _message_response(db, last) if last else None,
        "unread_count": _unread_count_for_membership(db, current_membership)
        if current_membership else 0,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
    }


def ensure_department_channels(db: Session, bank_id: int, created_by: Optional[int] = None) -> None:
    active_users = db.exec(
        select(User).where(
            User.bank_id == bank_id,
            User.is_active == True,  # noqa: E712
        )
    ).all()
    departments: Dict[str, List[User]] = {}
    for user in active_users:
        department = _clean_department(user.department)
        if department:
            departments.setdefault(department.lower(), []).append(user)

    for department_key, users in departments.items():
        title = _clean_department(users[0].department) or department_key.title()
        conversation = db.exec(
            select(MessengerConversation).where(
                MessengerConversation.bank_id == bank_id,
                MessengerConversation.type == "department",
                MessengerConversation.department == department_key,
            )
        ).first()
        if not conversation:
            conversation = MessengerConversation(
                bank_id=bank_id,
                type="department",
                title=title,
                department=department_key,
                created_by=created_by,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        expected_user_ids = {user.id for user in users if user.id is not None}
        memberships = _memberships_for_conversation(db, conversation.id)
        existing_user_ids = {membership.user_id for membership in memberships}
        for membership in memberships:
            if membership.user_id not in expected_user_ids:
                db.delete(membership)
        for user in users:
            if user.id not in existing_user_ids:
                db.add(
                    MessengerMembership(
                        bank_id=bank_id,
                        conversation_id=conversation.id,
                        user_id=user.id,
                        role="member",
                        source="department",
                    )
                )
        conversation.title = title
        conversation.updated_at = _now()
        db.add(conversation)
        db.commit()


def list_conversations(db: Session, current_user: User) -> List[Dict]:
    bank_id = require_bank_id(current_user)
    get_or_create_policy(db, bank_id)
    ensure_department_channels(db, bank_id, current_user.id)
    memberships = db.exec(
        select(MessengerMembership).where(
            MessengerMembership.bank_id == bank_id,
            MessengerMembership.user_id == current_user.id,
        )
    ).all()
    conversations = []
    for membership in memberships:
        conversation = db.get(MessengerConversation, membership.conversation_id)
        if conversation and conversation.is_active:
            conversations.append(conversation_response(db, conversation, current_user))
    return sorted(
        conversations,
        key=lambda item: item["last_message"]["created_at"] if item["last_message"] else item["updated_at"],
        reverse=True,
    )


def bootstrap(db: Session, current_user: User) -> Dict:
    bank_id = require_bank_id(current_user)
    policy = get_or_create_policy(db, bank_id)
    if not policy.enabled:
        return {
            "policy": _policy_response(policy),
            "current_user": _user_response(current_user),
            "conversations": [],
            "unread_count": 0,
        }
    conversations = list_conversations(db, current_user)
    return {
        "policy": _policy_response(policy),
        "current_user": _user_response(current_user),
        "conversations": conversations,
        "unread_count": get_total_unread_count(db, current_user),
    }


def list_directory(db: Session, current_user: User) -> List[Dict]:
    bank_id = require_bank_id(current_user)
    users = db.exec(
        select(User)
        .where(
            User.bank_id == bank_id,
            User.is_active == True,  # noqa: E712
        )
        .order_by(User.name)
    ).all()
    return [_user_response(user) for user in users if user.id != current_user.id]


def require_membership(
    db: Session,
    conversation_id: int,
    current_user: User,
) -> MessengerMembership:
    bank_id = require_bank_id(current_user)
    membership = db.exec(
        select(MessengerMembership).where(
            MessengerMembership.bank_id == bank_id,
            MessengerMembership.conversation_id == conversation_id,
            MessengerMembership.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation = db.get(MessengerConversation, conversation_id)
    if not conversation or conversation.bank_id != bank_id or not conversation.is_active:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return membership


def _conversation_or_404(db: Session, conversation_id: int, bank_id: int) -> MessengerConversation:
    conversation = db.get(MessengerConversation, conversation_id)
    if not conversation or conversation.bank_id != bank_id or not conversation.is_active:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def create_direct_conversation(
    db: Session,
    current_user: User,
    recipient_id: int,
) -> Dict:
    bank_id = require_bank_id(current_user)
    if current_user.id == recipient_id:
        raise HTTPException(status_code=400, detail="Choose another staff member")
    recipient = db.get(User, recipient_id)
    if not recipient or recipient.bank_id != bank_id or not recipient.is_active:
        raise HTTPException(status_code=404, detail="Recipient not found")

    direct_key = _direct_key(current_user.id, recipient_id)
    conversation = db.exec(
        select(MessengerConversation).where(
            MessengerConversation.bank_id == bank_id,
            MessengerConversation.type == "direct",
            MessengerConversation.direct_key == direct_key,
        )
    ).first()
    if not conversation:
        conversation = MessengerConversation(
            bank_id=bank_id,
            type="direct",
            title=f"{current_user.name}, {recipient.name}",
            direct_key=direct_key,
            created_by=current_user.id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        for user_id in [current_user.id, recipient_id]:
            db.add(
                MessengerMembership(
                    bank_id=bank_id,
                    conversation_id=conversation.id,
                    user_id=user_id,
                    role="member",
                    source="direct",
                )
            )
        db.commit()
        log_event(
            db,
            bank_id=bank_id,
            user_id=current_user.id,
            action="direct_conversation_create",
            resource_type="conversation",
            resource_id=str(conversation.id),
            metadata={"recipient_id": recipient_id},
        )
    return conversation_response(db, conversation, current_user)


def create_custom_group(
    db: Session,
    current_user: User,
    title: str,
    member_ids: List[int],
) -> Dict:
    bank_id = require_bank_id(current_user)
    policy = get_or_create_policy(db, bank_id)
    if current_user.role not in ADMIN_ROLES and not policy.allow_staff_groups:
        raise HTTPException(status_code=403, detail="Staff-created groups are disabled")

    unique_member_ids = sorted({member_id for member_id in member_ids if member_id != current_user.id})
    total_members = len(unique_member_ids) + 1
    if total_members > policy.max_group_members:
        raise HTTPException(status_code=400, detail=f"Group can include at most {policy.max_group_members} members")

    members = db.exec(select(User).where(User.id.in_(unique_member_ids))).all() if unique_member_ids else []
    if len(members) != len(unique_member_ids):
        raise HTTPException(status_code=404, detail="One or more members were not found")
    for member in members:
        if member.bank_id != bank_id or not member.is_active:
            raise HTTPException(status_code=404, detail="One or more members were not found")
        if not policy.allow_cross_department_groups and member.department != current_user.department:
            raise HTTPException(status_code=403, detail="Cross-department groups are disabled")

    conversation = MessengerConversation(
        bank_id=bank_id,
        type="custom",
        title=title,
        created_by=current_user.id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    db.add(
        MessengerMembership(
            bank_id=bank_id,
            conversation_id=conversation.id,
            user_id=current_user.id,
            role="owner",
            source="manual",
        )
    )
    for member_id in unique_member_ids:
        db.add(
            MessengerMembership(
                bank_id=bank_id,
                conversation_id=conversation.id,
                user_id=member_id,
                role="member",
                source="manual",
            )
        )
    db.commit()
    log_event(
        db,
        bank_id=bank_id,
        user_id=current_user.id,
        action="custom_group_create",
        resource_type="conversation",
        resource_id=str(conversation.id),
        metadata={"title": title, "member_ids": unique_member_ids},
    )
    return conversation_response(db, conversation, current_user)


def create_announcement_channel(db: Session, current_user: User, title: str) -> Dict:
    bank_id = require_bank_id(current_user)
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Only admins and managers can create announcements")
    conversation = MessengerConversation(
        bank_id=bank_id,
        type="announcement",
        title=title,
        created_by=current_user.id,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    active_users = db.exec(
        select(User).where(
            User.bank_id == bank_id,
            User.is_active == True,  # noqa: E712
        )
    ).all()
    for user in active_users:
        role = "admin" if user.role in MANAGER_ROLES else "readonly"
        db.add(
            MessengerMembership(
                bank_id=bank_id,
                conversation_id=conversation.id,
                user_id=user.id,
                role=role,
                source="system",
            )
        )
    db.commit()
    log_event(
        db,
        bank_id=bank_id,
        user_id=current_user.id,
        action="announcement_create",
        resource_type="conversation",
        resource_id=str(conversation.id),
        metadata={"title": title},
    )
    return conversation_response(db, conversation, current_user)


def list_messages(
    db: Session,
    current_user: User,
    conversation_id: int,
    limit: int = 100,
) -> List[Dict]:
    membership = require_membership(db, conversation_id, current_user)
    messages = db.exec(
        select(MessengerMessage)
        .where(MessengerMessage.conversation_id == membership.conversation_id)
        .where(MessengerMessage.deleted_at.is_(None))
        .order_by(MessengerMessage.created_at)
        .limit(limit)
    ).all()
    return [_message_response(db, message) for message in messages]


def mark_conversation_read(db: Session, current_user: User, conversation_id: int) -> Dict:
    membership = require_membership(db, conversation_id, current_user)
    last = _last_message(db, conversation_id)
    if last:
        membership.last_read_message_id = last.id
        membership.last_read_at = _now()
        db.add(membership)
        db.commit()
    return {"unread_count": get_total_unread_count(db, current_user)}


def send_message(db: Session, current_user: User, conversation_id: int, content: str) -> Dict:
    bank_id = require_bank_id(current_user)
    membership = require_membership(db, conversation_id, current_user)
    conversation = _conversation_or_404(db, conversation_id, bank_id)
    if conversation.type == "announcement" and membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Announcement channel is read-only")

    message = MessengerMessage(
        bank_id=bank_id,
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=content,
    )
    db.add(message)
    conversation.updated_at = _now()
    db.add(conversation)
    db.commit()
    db.refresh(message)
    membership.last_read_message_id = message.id
    membership.last_read_at = _now()
    db.add(membership)
    db.commit()
    log_event(
        db,
        bank_id=bank_id,
        user_id=current_user.id,
        action="message_send",
        resource_type="message",
        resource_id=str(message.id),
        metadata={"conversation_id": conversation.id, "conversation_type": conversation.type},
    )
    return _message_response(db, message)


def _messenger_upload_dir() -> str:
    return os.getenv("MESSENGER_UPLOAD_DIR", settings.MESSENGER_UPLOAD_DIR)


async def upload_attachment(
    db: Session,
    current_user: User,
    conversation_id: int,
    file: UploadFile,
    caption: Optional[str] = None,
) -> Dict:
    bank_id = require_bank_id(current_user)
    require_membership(db, conversation_id, current_user)
    policy = get_or_create_policy(db, bank_id)
    original_filename = file.filename or "attachment"
    extension = Path(original_filename).suffix.lower().lstrip(".")
    if extension not in _allowed_file_types(policy):
        raise HTTPException(status_code=400, detail="This file type is not allowed")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    max_bytes = policy.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {policy.max_file_size_mb} MB limit")

    upload_dir = os.path.join(_messenger_upload_dir(), str(bank_id), str(conversation_id))
    os.makedirs(upload_dir, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    stored_path = os.path.join(upload_dir, stored_filename)
    with open(stored_path, "wb") as buffer:
        buffer.write(content)

    message = MessengerMessage(
        bank_id=bank_id,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=(caption or original_filename).strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    attachment = MessengerAttachment(
        bank_id=bank_id,
        conversation_id=conversation_id,
        message_id=message.id,
        uploaded_by=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        stored_path=stored_path,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(attachment)
    membership = require_membership(db, conversation_id, current_user)
    membership.last_read_message_id = message.id
    membership.last_read_at = _now()
    conversation = _conversation_or_404(db, conversation_id, bank_id)
    conversation.updated_at = _now()
    db.add(membership)
    db.add(conversation)
    db.commit()
    db.refresh(attachment)
    log_event(
        db,
        bank_id=bank_id,
        user_id=current_user.id,
        action="attachment_upload",
        resource_type="attachment",
        resource_id=str(attachment.id),
        metadata={
            "conversation_id": conversation_id,
            "message_id": message.id,
            "original_filename": original_filename,
            "size_bytes": len(content),
            "content_type": attachment.content_type,
        },
    )
    return _message_response(db, message)


def get_attachment_for_member(
    db: Session,
    current_user: User,
    attachment_id: int,
) -> MessengerAttachment:
    bank_id = require_bank_id(current_user)
    attachment = db.get(MessengerAttachment, attachment_id)
    if not attachment or attachment.bank_id != bank_id or attachment.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    require_membership(db, attachment.conversation_id, current_user)
    log_event(
        db,
        bank_id=bank_id,
        user_id=current_user.id,
        action="attachment_view",
        resource_type="attachment",
        resource_id=str(attachment.id),
        metadata={"conversation_id": attachment.conversation_id},
    )
    return attachment
