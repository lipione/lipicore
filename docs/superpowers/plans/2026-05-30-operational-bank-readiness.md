# Operational Bank Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LipiCore deployment claims auditable through explicit health, backup, rollback, queue, GPU, and release evidence checks.

**Architecture:** Extend existing appliance health and deployment docs rather than introducing a new operations platform. Add a bank-readiness checklist endpoint/service, CLI-friendly evidence commands, and docs that distinguish pilot, department, and whole-bank readiness.

**Tech Stack:** FastAPI, existing appliance health service, Redis/Qdrant/PostgreSQL/MinIO health checks, pytest, deployment docs.

---

## File Structure

- Create: `backend/app/services/bank_readiness_service.py`
- Create: `backend/tests/test_bank_readiness_service.py`
- Modify: `backend/app/api/analytics.py`
- Modify: `frontend/src/pages/Analytics.jsx`
- Create: `docs/deployment/bank-readiness-checklist.md`
- Modify: `docs/sizing/production-tiers.md`

## Task 1: Add Bank Readiness Service

**Files:**
- Create: `backend/app/services/bank_readiness_service.py`
- Create: `backend/tests/test_bank_readiness_service.py`

- [ ] **Step 1: Write failing readiness tests**

Create `backend/tests/test_bank_readiness_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_bank_readiness_service.py -q
```

Expected: fail because service does not exist.

- [ ] **Step 3: Implement readiness service**

Create `backend/app/services/bank_readiness_service.py`:

```python
def evaluate_bank_readiness(snapshot: dict) -> dict:
    blockers = []
    warnings = []

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
```

- [ ] **Step 4: Run readiness tests**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_bank_readiness_service.py -q
```

Expected: `2 passed`.

## Task 2: Expose Readiness Endpoint

**Files:**
- Modify: `backend/app/api/analytics.py`
- Test: `backend/tests/test_appliance_health.py`

- [ ] **Step 1: Add failing API test**

Add to `backend/tests/test_appliance_health.py`:

```python
def test_bank_readiness_endpoint_requires_analytics_role(client, bank_admin_headers):
    response = client.get("/api/analytics/bank-readiness", headers=bank_admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "blockers" in payload
    assert "warnings" in payload
```

- [ ] **Step 2: Run API test to verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_appliance_health.py::test_bank_readiness_endpoint_requires_analytics_role -q
```

Expected: fail with `404`.

- [ ] **Step 3: Add endpoint**

In `backend/app/api/analytics.py`, add:

```python
@router.get("/bank-readiness")
def read_bank_readiness(current_user: User = Depends(get_current_analytics_user)):
    from ..services.bank_readiness_service import evaluate_bank_readiness

    snapshot = {
        "tls_enabled": settings.PUBLIC_ORIGIN.startswith("https://"),
        "backup_restore_drill_days_ago": None,
        "qdrant_snapshot_days_ago": None,
        "redis_persistence_enabled": False,
        "model_health_ok": True,
        "queue_depth": 0,
    }
    return evaluate_bank_readiness(snapshot)
```

Import `settings` and `User` if not already imported in that file.

- [ ] **Step 4: Run API test**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_appliance_health.py::test_bank_readiness_endpoint_requires_analytics_role -q
```

Expected: pass.

## Task 3: Add Deployment Checklist

**Files:**
- Create: `docs/deployment/bank-readiness-checklist.md`

- [ ] **Step 1: Create checklist document**

Create `docs/deployment/bank-readiness-checklist.md`:

```markdown
# Bank Readiness Checklist

Use this checklist before calling a LipiCore deployment bank-ready.

## Required Evidence

- TLS enabled for every staff-facing route.
- Strong `.env` secrets set outside git.
- PostgreSQL backup completed within the last 24 hours.
- PostgreSQL restore drill completed within the last 30 days.
- MinIO/object storage backup completed within the last 24 hours.
- Qdrant snapshot completed within the last 7 days.
- Redis persistence or accepted queue-loss policy documented.
- Model health endpoint checked after deployment.
- RAG evaluation gate passed on the bank's approved documents.
- Representative upload test completed for PDF, scanned PDF, DOCX, XLSX, PPTX, TXT/CSV, and image.
- Queue depth and GPU utilization reviewed.
- Rollback command tested in staging or documented for the release.

## Blockers

- No TLS.
- No restore drill.
- No approved-document evaluation run.
- Failed model health.
- Failed backup.
- Unknown admin access owner.
- Any cross-bank or cross-session data leak.
```

- [ ] **Step 2: Verify checklist terms**

Run:

```bash
rg -n "Required Evidence|Blockers|RAG evaluation gate|restore drill" docs/deployment/bank-readiness-checklist.md
```

Expected: all terms are found.

## Task 4: Update Production Tiers

**Files:**
- Modify: `docs/sizing/production-tiers.md`

- [ ] **Step 1: Add bank-readiness evidence note**

Add under Whole Bank:

```markdown
- Bank-readiness evidence: complete `docs/deployment/bank-readiness-checklist.md` before production go-live.
- A whole-bank claim requires retained evidence for backup restore, RAG evaluation, upload coverage, queue depth, GPU utilization, and rollback readiness.
```

- [ ] **Step 2: Verify docs**

Run:

```bash
rg -n "bank-readiness|backup restore|rollback readiness" docs/sizing/production-tiers.md
```

Expected: matching lines are present.

## Final Verification

- [ ] Run backend tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_bank_readiness_service.py backend/tests/test_appliance_health.py -q
```

- [ ] Run docs grep:

```bash
rg -n "Bank Readiness Checklist|bank-readiness evidence" docs
```

- [ ] Run diff check:

```bash
git diff --check
```

