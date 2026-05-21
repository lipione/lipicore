from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

ALLOWED_CHAT_MODES = {
    "ask_knowledge",
    "approved_knowledge",
    "analyze_file",
    "summarize",
    "draft",
    "translate",
    "compare",
}

class ChatMessageBase(BaseModel):
    role: str
    content: str
    sources_json: Optional[str] = None
    suggestions_json: Optional[str] = None

class ChatMessageResponse(ChatMessageBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class ChatSessionBase(BaseModel):
    title: str

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionResponse(ChatSessionBase):
    id: int
    bank_id: int
    user_id: int
    active_document_ids_json: str = "[]"
    session_summary: Optional[str] = None
    created_at: datetime
    messages: List[ChatMessageResponse] = []
    
    class Config:
        orm_mode = True

class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None
    language: Optional[str] = "en"
    active_document_ids: Optional[List[int]] = None
    model_override: Optional[str] = None
    mode: str = "ask_knowledge"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        if value not in ALLOWED_CHAT_MODES:
            raise ValueError(f"Unsupported chat mode: {value}")
        return value
