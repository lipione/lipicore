from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.market_utility import ExchangeRate, ExchangeRateBatch
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


BANKING_TIMEZONE = "Asia/Kathmandu"
RATE_UPDATE_POLICY = "Bank-published rates; treasury may update 2-3 times per business day."
ADMIN_ROLES = {"super_admin", "bank_admin"}


def _resolve_bank_id(current_user: User, requested_bank_id: Optional[int]) -> int:
    if current_user.role == "super_admin":
        bank_id = requested_bank_id or current_user.bank_id
        if bank_id is None:
            raise HTTPException(status_code=400, detail="No bank selected")
        return bank_id

    if requested_bank_id is not None and requested_bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Cannot access another bank's market utilities")
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return current_user.bank_id


def _batch_response(db: Session, batch: ExchangeRateBatch) -> dict:
    rates = db.exec(
        select(ExchangeRate)
        .where(ExchangeRate.batch_id == batch.id)
        .order_by(ExchangeRate.id)
    ).all()
    return {
        "id": batch.id,
        "bank_id": batch.bank_id,
        "source_name": batch.source_name,
        "notes": batch.notes,
        "published_at": batch.published_at,
        "created_by_user_id": batch.created_by_user_id,
        "created_at": batch.created_at,
        "rates": [
            {
                "id": rate.id,
                "batch_id": rate.batch_id,
                "currency_code": rate.currency_code,
                "currency_name": rate.currency_name,
                "unit": rate.unit,
                "buy_rate": rate.buy_rate,
                "sell_rate": rate.sell_rate,
                "middle_rate": rate.middle_rate,
            }
            for rate in rates
        ],
    }


def create_rate_batch(
    db: Session,
    *,
    current_user: User,
    requested_bank_id: Optional[int],
    source_name: str,
    notes: Optional[str],
    published_at: Optional[datetime],
    rates: list,
) -> dict:
    bank_id = _resolve_bank_id(current_user, requested_bank_id)
    require_feature_enabled(db, bank_id, "market_time")
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can publish exchange rates")
    if not rates:
        raise HTTPException(status_code=400, detail="At least one exchange rate is required")

    batch = ExchangeRateBatch(
        bank_id=bank_id,
        source_name=source_name.strip() or "Bank Treasury",
        notes=notes,
        published_at=published_at or datetime.utcnow(),
        created_by_user_id=current_user.id,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    for item in rates:
        db.add(
            ExchangeRate(
                bank_id=bank_id,
                batch_id=batch.id,
                currency_code=item.currency_code.strip().upper(),
                currency_name=item.currency_name.strip(),
                unit=item.unit,
                buy_rate=item.buy_rate,
                sell_rate=item.sell_rate,
                middle_rate=item.middle_rate,
            )
        )
    db.commit()
    return _batch_response(db, batch)


def list_rate_batches(
    db: Session,
    *,
    current_user: User,
    requested_bank_id: Optional[int] = None,
    limit: int = 10,
) -> list[dict]:
    bank_id = _resolve_bank_id(current_user, requested_bank_id)
    require_feature_enabled(db, bank_id, "market_time")
    clamped_limit = min(max(limit, 1), 50)
    batches = db.exec(
        select(ExchangeRateBatch)
        .where(ExchangeRateBatch.bank_id == bank_id)
        .order_by(ExchangeRateBatch.published_at.desc(), ExchangeRateBatch.id.desc())
        .limit(clamped_limit)
    ).all()
    return [_batch_response(db, batch) for batch in batches]


def get_market_summary(
    db: Session,
    *,
    current_user: User,
    requested_bank_id: Optional[int] = None,
) -> dict:
    bank_id = _resolve_bank_id(current_user, requested_bank_id)
    require_feature_enabled(db, bank_id, "market_time")
    local_now = datetime.now(ZoneInfo(BANKING_TIMEZONE))
    utc_now = datetime.now(timezone.utc)
    batches = list_rate_batches(db, current_user=current_user, requested_bank_id=bank_id, limit=1)
    return {
        "bank_id": bank_id,
        "timezone": BANKING_TIMEZONE,
        "server_time": local_now,
        "utc_time": utc_now,
        "business_date": local_now.date().isoformat(),
        "rate_update_policy": RATE_UPDATE_POLICY,
        "latest_rate_batch": batches[0] if batches else None,
    }
