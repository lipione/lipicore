from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from ..db.session import get_session
from ..models.user import User
from ..schemas.employee_directory import EmployeeDirectoryResult
from ..services.employee_directory_service import search_employee_directory
from .deps import get_current_user

router = APIRouter()


@router.get("", response_model=list[EmployeeDirectoryResult])
def search_directory(
    q: Optional[str] = None,
    department: Optional[str] = None,
    role: Optional[str] = None,
    branch: Optional[str] = None,
    expertise: Optional[str] = None,
    include_disabled: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    bank_id: Optional[int] = None,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return search_employee_directory(
        db,
        current_user=current_user,
        requested_bank_id=bank_id,
        q=q,
        department=department,
        role=role,
        branch=branch,
        expertise=expertise,
        include_disabled=include_disabled,
        limit=limit,
    )
