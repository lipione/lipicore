from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FeatureFlagResponse(BaseModel):
    id: Optional[int] = None
    bank_id: int
    feature_key: str
    enabled: bool
    configured_by_user_id: Optional[int] = None
    reason: Optional[str] = None
    updated_at: Optional[datetime] = None


class FeatureFlagListResponse(BaseModel):
    bank_id: int
    features: list[FeatureFlagResponse]


class FeatureFlagUpdate(BaseModel):
    enabled: bool
    reason: Optional[str] = None
