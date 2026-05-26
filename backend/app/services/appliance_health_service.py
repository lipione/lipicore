import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from sqlmodel import Session, select, func

from ..core.config import settings
from ..models.document import Document


def _service(status: str, detail: str | None = None, **extra) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status}
    if detail:
        payload["detail"] = detail
    payload.update(extra)
    return payload


def _document_counts(db: Session, bank_id: int) -> dict[str, Any]:
    total = db.exec(select(func.count(Document.id)).where(Document.bank_id == bank_id)).one() or 0
    status_rows = db.exec(
        select(Document.status, func.count(Document.id))
        .where(Document.bank_id == bank_id)
        .group_by(Document.status)
    ).all()
    version_rows = db.exec(
        select(Document.version_state, func.count(Document.id))
        .where(Document.bank_id == bank_id)
        .group_by(Document.version_state)
    ).all()
    scope_rows = db.exec(
        select(Document.document_scope, func.count(Document.id))
        .where(Document.bank_id == bank_id)
        .group_by(Document.document_scope)
    ).all()
    by_status = {str(status or "unknown"): int(count or 0) for status, count in status_rows}
    by_version_state = {str(state or "unknown"): int(count or 0) for state, count in version_rows}
    by_scope = {str(scope or "unknown"): int(count or 0) for scope, count in scope_rows}
    return {
        "total": int(total),
        "by_status": by_status,
        "by_version_state": by_version_state,
        "by_scope": by_scope,
        "needs_approval": int(by_status.get("ready", 0) + by_status.get("indexed", 0)),
        "failed": int(by_status.get("failed", 0)),
        "approved": int(by_status.get("approved", 0)),
    }


def _queue_length(queue_factory: Callable[[], Any] | None = None) -> tuple[int | None, dict[str, Any]]:
    try:
        if queue_factory is None:
            from .ingestion_queue import get_ingestion_queue

            queue_factory = get_ingestion_queue
        queue = queue_factory()
        queued_jobs = len(queue)
        return int(queued_jobs), _service(
            "healthy",
            queue_name=settings.INGESTION_QUEUE_NAME,
            queued_jobs=int(queued_jobs),
        )
    except Exception as exc:
        return None, _service(
            "degraded",
            f"{type(exc).__name__}: {exc}",
            queue_name=settings.INGESTION_QUEUE_NAME,
        )


def _qdrant_health(qdrant_client: Any | None = None) -> dict[str, Any]:
    try:
        if qdrant_client is None:
            from .qdrant_service import qdrant_client as default_client

            qdrant_client = default_client
        qdrant_client.get_collections()
        return _service("healthy", collection=settings.QDRANT_COLLECTION_NAME)
    except Exception as exc:
        return _service("degraded", f"{type(exc).__name__}: {exc}", collection=settings.QDRANT_COLLECTION_NAME)


def _storage_health(disk_paths: list[str] | None = None) -> dict[str, Any]:
    paths = disk_paths or [settings.UPLOAD_DIR, settings.CHAT_UPLOAD_DIR]
    results = []
    degraded = False
    for raw_path in paths:
        path = Path(raw_path)
        try:
            usage = shutil.disk_usage(path if path.exists() else path.parent)
            used_pct = round((usage.used / usage.total) * 100, 1) if usage.total else 0
            status = "healthy" if used_pct < 90 else "degraded"
            degraded = degraded or status == "degraded" or not path.exists()
            results.append({
                "path": str(path),
                "exists": path.exists(),
                "status": "degraded" if not path.exists() else status,
                "used_percent": used_pct,
                "free_bytes": usage.free,
                "total_bytes": usage.total,
            })
        except Exception as exc:
            degraded = True
            results.append({
                "path": str(path),
                "exists": False,
                "status": "degraded",
                "detail": f"{type(exc).__name__}: {exc}",
            })
    return _service("degraded" if degraded else "healthy", paths=results)


def collect_appliance_health(
    *,
    db: Session,
    bank_id: int,
    qdrant_client: Any | None = None,
    queue_factory: Callable[[], Any] | None = None,
    disk_paths: list[str] | None = None,
) -> dict[str, Any]:
    services: dict[str, Any] = {}
    documents: dict[str, Any]
    try:
        documents = _document_counts(db, bank_id)
        services["database"] = _service("healthy")
    except Exception as exc:
        documents = {"total": 0, "by_status": {}, "by_version_state": {}, "by_scope": {}}
        services["database"] = _service("degraded", f"{type(exc).__name__}: {exc}")

    queued_jobs, redis_status = _queue_length(queue_factory)
    services["redis"] = redis_status
    services["qdrant"] = _qdrant_health(qdrant_client)
    services["storage"] = _storage_health(disk_paths)

    overall = "healthy"
    if any(service.get("status") != "healthy" for service in services.values()):
        overall = "degraded"

    return {
        "status": overall,
        "checked_at": datetime.utcnow().isoformat(),
        "services": services,
        "documents": documents,
        "ingestion": {
            "queue_name": settings.INGESTION_QUEUE_NAME,
            "queued_jobs": queued_jobs,
            "failed_documents": documents.get("failed", 0),
            "needs_approval": documents.get("needs_approval", 0),
        },
    }
