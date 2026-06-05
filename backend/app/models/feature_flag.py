from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class BankFeatureFlag(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("bank_id", "feature_key", name="uq_bank_feature_flag_bank_feature"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    feature_key: str = Field(index=True)
    enabled: bool = Field(default=False)
    configured_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    reason: Optional[str] = None
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
