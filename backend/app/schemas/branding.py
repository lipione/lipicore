import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


DEFAULT_ALLOWED_MODES = ["ask_knowledge", "analyze_file", "summarize", "draft", "translate", "compare"]


class BrandingBase(BaseModel):
    product_name: str = "BankAi"
    bank_name: str = "Your Bank"
    logo_url: Optional[str] = None
    primary_color: str = "#17324d"
    accent_color: str = "#c7902c"
    welcome_message: str = "Ask approved bank knowledge, analyze internal files, and draft staff-ready answers."
    support_contact: Optional[str] = None
    disclaimer: str = "Internal staff use only. Verify critical outputs against approved source documents."
    allowed_modes: list[str] = Field(default_factory=lambda: DEFAULT_ALLOWED_MODES.copy())

    @field_validator("allowed_modes")
    @classmethod
    def allowed_modes_must_not_be_empty(cls, value):
        if not value:
            raise ValueError("At least one assistant mode must be enabled")
        return value


class BrandingUpdate(BaseModel):
    product_name: Optional[str] = None
    bank_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    welcome_message: Optional[str] = None
    support_contact: Optional[str] = None
    disclaimer: Optional[str] = None
    allowed_modes: Optional[list[str]] = None

    @field_validator("allowed_modes")
    @classmethod
    def allowed_modes_must_not_be_empty(cls, value):
        if value is not None and not value:
            raise ValueError("At least one assistant mode must be enabled")
        return value


class BrandingResponse(BrandingBase):
    bank_id: Optional[int] = None
    updated_at: Optional[datetime] = None


def parse_allowed_modes(raw: str | None) -> list[str]:
    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return DEFAULT_ALLOWED_MODES.copy()
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed) or not parsed:
        return DEFAULT_ALLOWED_MODES.copy()
    return parsed
