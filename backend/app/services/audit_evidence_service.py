import json

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.audit_evidence import AuditEvidencePack
from ..models.user import User
from ..services.feature_flag_service import require_feature_enabled


ADMIN_ROLES = {"super_admin", "bank_admin", "auditor", "data_auditor"}


def _require_bank(user: User) -> int:
    if user.bank_id is None:
        raise HTTPException(status_code=400, detail="No bank selected")
    return user.bank_id


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _response(pack: AuditEvidencePack) -> dict:
    return {
        "id": pack.id,
        "bank_id": pack.bank_id,
        "title": pack.title,
        "source_type": pack.source_type,
        "source_id": pack.source_id,
        "summary": pack.summary,
        "included_items": _json_list(pack.included_items_json),
        "created_by_user_id": pack.created_by_user_id,
        "created_at": pack.created_at,
    }


def create_pack(db: Session, *, current_user: User, payload) -> dict:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "audit_evidence_pack")
    pack = AuditEvidencePack(
        bank_id=bank_id,
        title=payload.title.strip(),
        source_type=payload.source_type,
        source_id=payload.source_id,
        summary=payload.summary,
        included_items_json=json.dumps(payload.included_items),
        created_by_user_id=current_user.id,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return _response(pack)


def list_packs(db: Session, *, current_user: User, scope: str = "mine") -> list[dict]:
    bank_id = _require_bank(current_user)
    require_feature_enabled(db, bank_id, "audit_evidence_pack")
    query = select(AuditEvidencePack).where(AuditEvidencePack.bank_id == bank_id)
    if scope == "bank":
        if current_user.role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Only audit/admin roles can list bank-wide evidence packs")
    else:
        query = query.where(AuditEvidencePack.created_by_user_id == current_user.id)
    query = query.order_by(AuditEvidencePack.created_at.desc(), AuditEvidencePack.id.desc())
    return [_response(pack) for pack in db.exec(query).all()]
