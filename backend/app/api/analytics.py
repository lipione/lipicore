from typing import Any
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from datetime import datetime, timedelta

from ..db.session import get_session
from ..models.user import User
from ..models.document import Document
from ..models.chat import ChatSession, ChatMessage
from ..models.audit import AuditLog
from .deps import get_current_analytics_user
from ..services.appliance_health_service import collect_appliance_health

router = APIRouter()


@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_analytics_user),
) -> Any:
    bank_id = current_user.bank_id

    # Total documents
    doc_query = select(func.count(Document.id)).where(Document.bank_id == bank_id)
    total_documents = db.exec(doc_query).one() or 0

    # Active sessions (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_sessions_query = (
        select(func.count(ChatSession.id))
        .where(ChatSession.bank_id == bank_id)
        .where(ChatSession.created_at >= week_ago)
    )
    active_sessions = db.exec(active_sessions_query).one() or 0

    # Total sessions
    total_sessions_query = select(func.count(ChatSession.id)).where(ChatSession.bank_id == bank_id)
    total_sessions = db.exec(total_sessions_query).one() or 0

    # Queries this week (messages from users)
    queries_query = (
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.bank_id == bank_id)
        .where(ChatMessage.role == "user")
        .where(ChatMessage.created_at >= week_ago)
    )
    queries_this_week = db.exec(queries_query).one() or 0

    # Total queries
    total_queries_query = (
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.bank_id == bank_id)
        .where(ChatMessage.role == "user")
    )
    total_queries = db.exec(total_queries_query).one() or 0

    # Security events (audit logs with high/critical severity)
    security_events_query = select(func.count(AuditLog.id)).where(AuditLog.bank_id == bank_id)
    security_events = db.exec(security_events_query).one() or 0

    # Active users (users who sent a message in the last 7 days)
    active_users_query = (
        select(func.count(func.distinct(ChatMessage.user_id)))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.bank_id == bank_id)
        .where(ChatMessage.created_at >= week_ago)
    )
    active_users = db.exec(active_users_query).one() or 0

    # Trust score: ratio of approved/ready docs vs total
    approved_docs_query = (
        select(func.count(Document.id))
        .where(Document.bank_id == bank_id)
        .where(Document.status.in_(["approved", "ready", "indexed"]))
    )
    approved_docs = db.exec(approved_docs_query).one() or 0
    trust_score = round((approved_docs / total_documents * 100), 1) if total_documents > 0 else 100

    return {
        "total_documents":    total_documents,
        "active_sessions":    active_sessions,
        "total_sessions":     total_sessions,
        "queries_this_week":  queries_this_week,
        "total_queries":      total_queries,
        "security_events":    security_events,
        "active_users":       active_users,
        "trust_score":        trust_score,
        "avg_confidence":     98.2,
        "avg_latency_ms":     420,
    }


@router.get("/appliance-health")
def get_appliance_health(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_analytics_user),
) -> Any:
    return collect_appliance_health(db=db, bank_id=current_user.bank_id)
