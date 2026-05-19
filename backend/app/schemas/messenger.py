from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class MessengerUserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: Optional[str] = None


class MessengerPolicyResponse(BaseModel):
    enabled: bool
    allow_staff_groups: bool
    allow_cross_department_groups: bool
    allow_web_downloads: bool
    max_group_members: int
    max_file_size_mb: int
    allowed_file_types: List[str]
    retention_days: int


class MessengerAttachmentResponse(BaseModel):
    id: int
    original_filename: str
    stored_path: str
    content_type: str
    size_bytes: int
    created_at: datetime
    download_url: Optional[str] = None


class MessengerMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: MessengerUserResponse
    content: str
    status: str
    created_at: datetime
    attachments: List[MessengerAttachmentResponse] = []


class MessengerConversationResponse(BaseModel):
    id: int
    type: str
    title: str
    department: Optional[str] = None
    role: str
    members: List[MessengerUserResponse]
    last_message: Optional[MessengerMessageResponse] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime


class MessengerBootstrapResponse(BaseModel):
    policy: MessengerPolicyResponse
    current_user: MessengerUserResponse
    conversations: List[MessengerConversationResponse]
    unread_count: int


class DirectConversationCreate(BaseModel):
    recipient_id: int


class CustomConversationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=80)
    member_ids: List[int] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Group title is required")
        return cleaned


class AnnouncementConversationCreate(BaseModel):
    title: str = Field(min_length=2, max_length=80)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Announcement title is required")
        return cleaned


class MessengerMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message content is required")
        return cleaned


class MessengerUnreadCountResponse(BaseModel):
    unread_count: int
