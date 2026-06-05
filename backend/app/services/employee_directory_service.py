import json
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.employee_profile import EmployeeProfile
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin"}


def _resolve_bank_id(current_user: User, requested_bank_id: Optional[int]) -> int:
    if current_user.role == "super_admin":
        bank_id = requested_bank_id or current_user.bank_id
        if bank_id is None:
            raise HTTPException(status_code=400, detail="No bank selected")
        return bank_id

    if requested_bank_id is not None and requested_bank_id != current_user.bank_id:
        raise HTTPException(status_code=403, detail="Cannot search another bank's employee directory")
    if current_user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return current_user.bank_id


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if item is not None]


def _matches(value: str | None, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.casefold() in (value or "").casefold()


def _searchable_text(user: User, profile: EmployeeProfile | None) -> str:
    profile_parts: list[str] = []
    expertise_tags = _json_list(profile.expertise_tags_json if profile else None)
    escalation_areas = _json_list(profile.escalation_areas_json if profile else None)
    if profile:
        profile_parts = [
            profile.branch or "",
            profile.job_title or "",
            profile.phone_extension or "",
            profile.availability_status or "",
            profile.public_notes or "",
            " ".join(expertise_tags),
            " ".join(escalation_areas),
        ]
    return " ".join([
        user.name,
        user.email,
        user.role,
        user.department or "",
        *profile_parts,
    ]).casefold()


def _to_result(user: User, profile: EmployeeProfile | None, current_user: User) -> dict:
    expertise_tags = _json_list(profile.expertise_tags_json if profile else None)
    escalation_areas = _json_list(profile.escalation_areas_json if profile else None)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "department": user.department,
        "branch": profile.branch if profile else None,
        "job_title": profile.job_title if profile else None,
        "phone_extension": profile.phone_extension if profile else None,
        "supervisor_user_id": profile.supervisor_user_id if profile else None,
        "expertise_tags": expertise_tags,
        "escalation_areas": escalation_areas,
        "availability_status": profile.availability_status if profile else "available",
        "is_active": user.is_active,
        "can_message": bool(user.is_active and user.id != current_user.id),
    }


def search_employee_directory(
    db: Session,
    *,
    current_user: User,
    requested_bank_id: Optional[int] = None,
    q: Optional[str] = None,
    department: Optional[str] = None,
    role: Optional[str] = None,
    branch: Optional[str] = None,
    expertise: Optional[str] = None,
    include_disabled: bool = False,
    limit: int = 50,
) -> list[dict]:
    bank_id = _resolve_bank_id(current_user, requested_bank_id)
    require_feature_enabled(db, bank_id, "employee_directory")

    if include_disabled and current_user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Only admins can include disabled employees")

    clamped_limit = min(max(limit, 1), 100)
    users = db.exec(select(User).where(User.bank_id == bank_id)).all()
    profiles = db.exec(select(EmployeeProfile).where(EmployeeProfile.bank_id == bank_id)).all()
    profiles_by_user_id = {profile.user_id: profile for profile in profiles}

    results: list[dict] = []
    q_normalized = (q or "").strip().casefold()
    for user in users:
        profile = profiles_by_user_id.get(user.id)
        if not include_disabled and not user.is_active:
            continue
        if department and not _matches(user.department, department):
            continue
        if role and user.role != role:
            continue
        if branch and not _matches(profile.branch if profile else None, branch):
            continue
        if expertise:
            expertise_text = " ".join(_json_list(profile.expertise_tags_json if profile else None))
            if not _matches(expertise_text, expertise):
                continue
        if q_normalized and q_normalized not in _searchable_text(user, profile):
            continue

        results.append(_to_result(user, profile, current_user))
        if len(results) >= clamped_limit:
            break

    return results
