from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.market_utility import (
    ExchangeRateBatchCreate,
    ExchangeRateBatchResponse,
    MarketUtilitySummary,
)
from ..services.audit_service import log_audit_event
from ..services.market_utility_service import create_rate_batch, get_market_summary, list_rate_batches
from .deps import get_current_user

router = APIRouter()


@router.get("/summary", response_model=MarketUtilitySummary)
def read_market_summary(
    bank_id: Optional[int] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_market_summary(db, current_user=current_user, requested_bank_id=bank_id)


@router.get("/rate-batches", response_model=list[ExchangeRateBatchResponse])
def read_rate_batches(
    bank_id: Optional[int] = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_rate_batches(db, current_user=current_user, requested_bank_id=bank_id, limit=limit)


@router.post("/rate-batches", response_model=ExchangeRateBatchResponse)
def publish_rate_batch(
    payload: ExchangeRateBatchCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    batch = create_rate_batch(
        db,
        current_user=current_user,
        requested_bank_id=payload.bank_id,
        source_name=payload.source_name,
        notes=payload.notes,
        published_at=payload.published_at,
        rates=payload.rates,
    )
    log_audit_event(
        db=db,
        action="exchange_rate_batch_publish",
        resource_type="exchange_rate_batch",
        resource_id=str(batch["id"]),
        bank_id=batch["bank_id"],
        user_id=current_user.id,
        metadata={
            "source_name": batch["source_name"],
            "rate_count": len(batch["rates"]),
        },
    )
    return batch
