from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExchangeRateInput(BaseModel):
    currency_code: str
    currency_name: str
    unit: int = Field(default=1, ge=1)
    buy_rate: float
    sell_rate: float
    middle_rate: Optional[float] = None


class ExchangeRateResponse(ExchangeRateInput):
    id: int
    batch_id: int


class ExchangeRateBatchCreate(BaseModel):
    bank_id: Optional[int] = None
    source_name: str = "Bank Treasury"
    notes: Optional[str] = None
    published_at: Optional[datetime] = None
    rates: list[ExchangeRateInput]


class ExchangeRateBatchResponse(BaseModel):
    id: int
    bank_id: int
    source_name: str
    notes: Optional[str] = None
    published_at: datetime
    created_by_user_id: Optional[int] = None
    created_at: datetime
    rates: list[ExchangeRateResponse] = []


class MarketUtilitySummary(BaseModel):
    bank_id: int
    timezone: str
    server_time: datetime
    utc_time: datetime
    business_date: str
    rate_update_policy: str
    latest_rate_batch: Optional[ExchangeRateBatchResponse] = None
