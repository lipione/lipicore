from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..db.session import get_session
from ..models.bank import Bank
from ..models.user import User
from ..schemas.feature_flag import FeatureFlagListResponse, FeatureFlagResponse, FeatureFlagUpdate
from ..services.audit_service import log_audit_event
from ..services.feature_flag_service import list_feature_flags, set_feature_flag
from .deps import get_current_bank_admin, get_current_user

router = APIRouter()


def _resolve_bank_id(requested_bank_id: int | None, current_user: User) -> int:
    if current_user.role == "super_admin":
        bank_id = requested_bank_id or current_user.bank_id
        if bank_id is None:
            raise HTTPException(status_code=400, detail="No bank selected")
        return bank_id
    if requested_bank_id is not None and requested_bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Cannot read another bank's feature flags")
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return current_user.bank_id


def _to_response(flag) -> FeatureFlagResponse:
    return FeatureFlagResponse(
        id=flag.id,
        bank_id=flag.bank_id,
        feature_key=flag.feature_key,
        enabled=flag.enabled,
        configured_by_user_id=flag.configured_by_user_id,
        reason=flag.reason,
        updated_at=flag.updated_at,
    )


@router.get("", response_model=FeatureFlagListResponse)
def read_feature_flags(
    bank_id: int | None = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_bank_admin),
) -> Any:
    resolved_bank_id = _resolve_bank_id(bank_id, current_user)
    bank = db.get(Bank, resolved_bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    flags = list_feature_flags(db, resolved_bank_id)
    return FeatureFlagListResponse(
        bank_id=resolved_bank_id,
        features=[_to_response(flag) for flag in flags],
    )


@router.get("/effective", response_model=FeatureFlagListResponse)
def read_effective_feature_flags(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    flags = list_feature_flags(db, current_user.bank_id)
    return FeatureFlagListResponse(
        bank_id=current_user.bank_id,
        features=[_to_response(flag) for flag in flags],
    )


@router.patch("/{bank_id}/{feature_key}", response_model=FeatureFlagResponse)
def update_feature_flag(
    *,
    bank_id: int,
    feature_key: str,
    payload: FeatureFlagUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_bank_admin),
) -> Any:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can change bank feature flags")
    bank = db.get(Bank, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    flag = set_feature_flag(
        db,
        bank_id=bank_id,
        feature_key=feature_key,
        enabled=payload.enabled,
        configured_by_user_id=current_user.id,
        reason=payload.reason,
    )
    log_audit_event(
        db=db,
        action="feature_flag_update",
        resource_type="feature_flag",
        resource_id=feature_key,
        bank_id=bank_id,
        user_id=current_user.id,
        metadata={
            "feature_key": feature_key,
            "enabled": payload.enabled,
            "reason": payload.reason,
        },
    )
    return _to_response(flag)
