from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BrandingSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", unique=True, index=True)
    product_name: str = Field(default="BankAi")
    bank_name: str = Field(default="Your Bank")
    logo_url: Optional[str] = None
    primary_color: str = Field(default="#17324d")
    accent_color: str = Field(default="#c7902c")
    welcome_message: str = Field(
        default="Ask approved bank knowledge, analyze internal files, and draft staff-ready answers."
    )
    support_contact: Optional[str] = None
    disclaimer: str = Field(default="Internal staff use only. Verify critical outputs against approved source documents.")
    allowed_modes_json: str = Field(default='["ask_knowledge","approved_knowledge","analyze_file","summarize","draft","translate","compare"]')
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
