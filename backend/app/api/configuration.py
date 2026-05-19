import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db.session import get_session
from ..models.bank import Bank
from ..models.branding import BrandingSettings
from ..models.user import User
from ..schemas.branding import BrandingResponse, BrandingUpdate, DEFAULT_ALLOWED_MODES, parse_allowed_modes
from .deps import get_current_bank_admin

router = APIRouter()


def _to_response(settings: BrandingSettings | None, bank: Bank | None = None) -> BrandingResponse:
    if not settings:
        return BrandingResponse(bank_id=bank.id if bank else None, bank_name=bank.name if bank else "Your Bank")
    return BrandingResponse(
        bank_id=settings.bank_id,
        product_name=settings.product_name,
        bank_name=settings.bank_name,
        logo_url=settings.logo_url,
        primary_color=settings.primary_color,
        accent_color=settings.accent_color,
        welcome_message=settings.welcome_message,
        support_contact=settings.support_contact,
        disclaimer=settings.disclaimer,
        allowed_modes=parse_allowed_modes(settings.allowed_modes_json),
        updated_at=settings.updated_at,
    )


@router.get("/branding", response_model=BrandingResponse)
def read_public_branding(
    bank_code: Optional[str] = None,
    db: Session = Depends(get_session),
) -> Any:
    bank = None
    if bank_code:
        bank = db.exec(select(Bank).where(Bank.code == bank_code)).first()
        if not bank:
            raise HTTPException(status_code=404, detail="Bank not found")
    else:
        bank = db.exec(select(Bank).where(Bank.status == "active").order_by(Bank.id)).first()

    if not bank:
        return BrandingResponse(allowed_modes=DEFAULT_ALLOWED_MODES.copy())

    settings = db.exec(select(BrandingSettings).where(BrandingSettings.bank_id == bank.id)).first()
    return _to_response(settings, bank)


@router.patch("/branding/{bank_id}", response_model=BrandingResponse)
def update_branding(
    *,
    bank_id: int,
    branding_in: BrandingUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_bank_admin),
) -> Any:
    if current_user.role != "super_admin" and current_user.bank_id != bank_id:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")

    bank = db.get(Bank, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    settings = db.exec(select(BrandingSettings).where(BrandingSettings.bank_id == bank_id)).first()
    if not settings:
        settings = BrandingSettings(bank_id=bank_id, bank_name=bank.name)

    update_data = branding_in.model_dump(exclude_unset=True)
    allowed_modes = update_data.pop("allowed_modes", None)
    for field, value in update_data.items():
        setattr(settings, field, value)
    if allowed_modes is not None:
        settings.allowed_modes_json = json.dumps(allowed_modes)
    settings.updated_at = datetime.utcnow()

    db.add(settings)
    db.commit()
    db.refresh(settings)
    return _to_response(settings, bank)
