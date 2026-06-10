from datetime import datetime, timedelta

from sqlmodel import Session, select

from ..core.config import settings
from ..models.audit import AuditLog, SecurityEvent
from ..models.user import User


def _lockout_window_start(db: Session, user: User) -> datetime:
    window_start = datetime.utcnow() - timedelta(minutes=settings.AUTH_ACCOUNT_LOCKOUT_WINDOW_MINUTES)
    last_success = db.exec(
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .where(AuditLog.action == "login")
        .order_by(AuditLog.created_at.desc())
    ).first()
    if last_success and last_success.created_at > window_start:
        return last_success.created_at
    return window_start


def recent_failed_login_count(db: Session, user: User) -> int:
    window_start = _lockout_window_start(db, user)
    return len(
        db.exec(
            select(SecurityEvent)
            .where(SecurityEvent.user_id == user.id)
            .where(SecurityEvent.event_type == "failed_login")
            .where(SecurityEvent.created_at >= window_start)
        ).all()
    )


def is_account_login_locked(db: Session, user: User) -> bool:
    return recent_failed_login_count(db, user) >= settings.AUTH_ACCOUNT_LOCKOUT_MAX_FAILURES
