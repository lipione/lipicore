from datetime import datetime
import os

from fastapi import HTTPException
from sqlmodel import Session, select

from ..models.feature_flag import BankFeatureFlag


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


DEFAULT_NEW_FEATURE_FLAGS: dict[str, bool] = {
    "employee_directory": False,
    "market_time": False,
    "staff_inbox": False,
    "notifications": False,
    "ceo_messages": False,
    "knowledge_gaps": False,
    "policy_changes": False,
    "audit_evidence_pack": False,
    "complaint_workspace": False,
    "circular_impact_analyzer": False,
    "branch_response_builder": False,
    "kyc_case_prep": False,
    "checklist_validator": False,
    "citation_nli_verification": _env_bool("CITATION_NLI_ENABLED", "false"),
    "citation_semantic_verification": _env_bool("CITATION_SEMANTIC_VERIFICATION_ENABLED", "true"),
}


def validate_feature_key(feature_key: str) -> str:
    normalized = (feature_key or "").strip()
    if normalized not in DEFAULT_NEW_FEATURE_FLAGS:
        raise HTTPException(status_code=400, detail=f"Unknown feature key: {feature_key}")
    return normalized


def _default_flag(bank_id: int, feature_key: str) -> BankFeatureFlag:
    return BankFeatureFlag(
        bank_id=bank_id,
        feature_key=feature_key,
        enabled=DEFAULT_NEW_FEATURE_FLAGS[feature_key],
    )


def list_feature_flags(db: Session, bank_id: int) -> list[BankFeatureFlag]:
    rows = db.exec(
        select(BankFeatureFlag).where(BankFeatureFlag.bank_id == bank_id)
    ).all()
    by_key = {row.feature_key: row for row in rows}
    flags: list[BankFeatureFlag] = []
    for feature_key in DEFAULT_NEW_FEATURE_FLAGS:
        flags.append(by_key.get(feature_key) or _default_flag(bank_id, feature_key))
    return flags


def is_feature_enabled(db: Session, bank_id: int | None, feature_key: str) -> bool:
    if bank_id is None:
        return False
    feature_key = validate_feature_key(feature_key)
    row = db.exec(
        select(BankFeatureFlag).where(
            BankFeatureFlag.bank_id == bank_id,
            BankFeatureFlag.feature_key == feature_key,
        )
    ).first()
    return bool(row.enabled) if row else DEFAULT_NEW_FEATURE_FLAGS[feature_key]


def set_feature_flag(
    db: Session,
    *,
    bank_id: int,
    feature_key: str,
    enabled: bool,
    configured_by_user_id: int | None,
    reason: str | None = None,
) -> BankFeatureFlag:
    feature_key = validate_feature_key(feature_key)
    row = db.exec(
        select(BankFeatureFlag).where(
            BankFeatureFlag.bank_id == bank_id,
            BankFeatureFlag.feature_key == feature_key,
        )
    ).first()
    if not row:
        row = BankFeatureFlag(bank_id=bank_id, feature_key=feature_key)
    row.enabled = enabled
    row.configured_by_user_id = configured_by_user_id
    row.reason = reason
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def require_feature_enabled(db: Session, bank_id: int | None, feature_key: str) -> None:
    feature_key = validate_feature_key(feature_key)
    if not is_feature_enabled(db, bank_id, feature_key):
        raise HTTPException(
            status_code=403,
            detail={"code": "feature_disabled", "feature": feature_key},
        )
