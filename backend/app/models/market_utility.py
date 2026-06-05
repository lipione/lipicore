from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ExchangeRateBatch(SQLModel, table=True):
    __tablename__ = "exchangeratebatch"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    source_name: str = Field(default="Bank Treasury")
    notes: Optional[str] = None
    published_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExchangeRate(SQLModel, table=True):
    __tablename__ = "exchangerate"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    batch_id: int = Field(foreign_key="exchangeratebatch.id", index=True)
    currency_code: str = Field(index=True)
    currency_name: str
    unit: int = Field(default=1)
    buy_rate: float
    sell_rate: float
    middle_rate: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BankingCalendarEvent(SQLModel, table=True):
    __tablename__ = "bankingcalendarevent"

    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    title: str
    event_type: str = Field(default="cutoff", index=True)
    starts_at: datetime
    ends_at: Optional[datetime] = None
    timezone: str = Field(default="Asia/Kathmandu")
    branch: Optional[str] = Field(default=None, index=True)
    notes: Optional[str] = None
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
