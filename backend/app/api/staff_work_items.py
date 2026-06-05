from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.staff_work_item import StaffWorkItemCreate, StaffWorkItemResponse, StaffWorkItemUpdate
from ..services.staff_work_item_service import create_work_item, list_work_items, update_work_item
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[StaffWorkItemResponse])
def read_work_items(
    scope: str = "mine",
    status: Optional[str] = None,
    include_closed: bool = True,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return list_work_items(db, current_user=current_user, scope=scope, status=status, include_closed=include_closed)


@router.post("", response_model=StaffWorkItemResponse)
def create_item(
    payload: StaffWorkItemCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_work_item(db, current_user=current_user, payload=payload)


@router.patch("/{item_id}", response_model=StaffWorkItemResponse)
def update_item(
    item_id: int,
    payload: StaffWorkItemUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return update_work_item(db, current_user=current_user, item_id=item_id, payload=payload)
