from app.services.bank_readiness_service import evaluate_bank_readiness


def test_bank_readiness_requires_backup_restore_and_tls():
    result = evaluate_bank_readiness({
        "tls_enabled": False,
        "backup_restore_drill_days_ago": 10,
        "qdrant_snapshot_days_ago": 1,
        "redis_persistence_enabled": True,
        "model_health_ok": True,
        "queue_depth": 0,
    })

    assert result["status"] == "blocked"
    assert "tls_not_enabled" in result["blockers"]


def test_bank_readiness_marks_ready_when_required_controls_present():
    result = evaluate_bank_readiness({
        "tls_enabled": True,
        "backup_restore_drill_days_ago": 20,
        "qdrant_snapshot_days_ago": 2,
        "redis_persistence_enabled": True,
        "model_health_ok": True,
        "queue_depth": 3,
    })

    assert result["status"] == "ready"
    assert result["blockers"] == []
