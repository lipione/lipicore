from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.policy_change import PolicyChangeCreate, PolicyChangeResponse
from ..services.policy_change_service import acknowledge_policy_change, create_policy_change, list_policy_changes
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[PolicyChangeResponse])
def read_policy_changes(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_policy_changes(db, current_user=current_user)


@router.post("", response_model=PolicyChangeResponse)
def create_change(
    payload: PolicyChangeCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_policy_change(db, current_user=current_user, payload=payload)


@router.patch("/{change_id}/acknowledge", response_model=PolicyChangeResponse)
def acknowledge_change(
    change_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return acknowledge_policy_change(db, current_user=current_user, change_id=change_id)
