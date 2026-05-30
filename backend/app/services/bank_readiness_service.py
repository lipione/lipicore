def evaluate_bank_readiness(snapshot: dict) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []

    if not snapshot.get("tls_enabled"):
        blockers.append("tls_not_enabled")
    if snapshot.get("backup_restore_drill_days_ago") is None:
        blockers.append("backup_restore_drill_missing")
    elif snapshot["backup_restore_drill_days_ago"] > 30:
        warnings.append("backup_restore_drill_stale")
    if snapshot.get("qdrant_snapshot_days_ago") is None:
        blockers.append("qdrant_snapshot_missing")
    elif snapshot["qdrant_snapshot_days_ago"] > 7:
        warnings.append("qdrant_snapshot_stale")
    if not snapshot.get("redis_persistence_enabled"):
        warnings.append("redis_persistence_not_confirmed")
    if not snapshot.get("model_health_ok"):
        blockers.append("model_health_failed")
    if snapshot.get("queue_depth", 0) > 50:
        warnings.append("queue_depth_high")

    return {
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "warnings": warnings,
    }
