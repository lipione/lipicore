# Bare-Metal Phase 1 Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden LipiCore as a dedicated single-bank bare-metal appliance by closing the Phase 1 gaps around document governance, per-bank RAG isolation, source inspection, citation/evaluation controls, exact-query behavior, and appliance monitoring.

**Architecture:** Keep the existing FastAPI, React/Vite, PostgreSQL, Qdrant, Redis/RQ, and vLLM architecture. Phase 1 adds small production-readiness APIs and UI surfaces around the already-working RAG core instead of changing ingestion or model serving architecture.

**Tech Stack:** FastAPI, SQLModel, PostgreSQL, Qdrant, Redis/RQ, React/Vite, Tailwind-style utility CSS, pytest.

---

## Current State

- Document ingestion, chunking, BGE-M3 embeddings, Qdrant indexing, approval, citation verifier, RAG evaluation API/page, and query rewrite exist.
- Gaps to close first:
  - Governance metadata changes are not exposed as a controlled API.
  - Disabling/archiving/superseding documents should update chunks and Qdrant payloads consistently.
  - Staff/admins need a bank-scoped source-detail endpoint for exact source inspection.
  - Monitoring needs an appliance health API beyond the high-level analytics summary.
  - Frontend Analytics should show live service/queue/document health instead of only static/product metrics.

## Files

- Modify: `backend/app/api/documents.py`
  - Add governance metadata/state endpoints and source-detail endpoint.
- Create: `backend/app/services/appliance_health_service.py`
  - Collect DB, Qdrant, Redis/RQ, disk, and document status health.
- Modify: `backend/app/api/analytics.py`
  - Add `/api/analytics/appliance-health`.
- Test: `backend/tests/test_document_governance_phase1.py`
  - Cover bank isolation, governance updates, state updates, and source viewer.
- Test: `backend/tests/test_appliance_health.py`
  - Cover health response shape and degraded dependency handling.
- Modify: `frontend/src/pages/Analytics.jsx`
  - Show appliance health cards and document/queue status.
- Modify: `frontend/src/components/chat/SourceEvidencePanel.jsx`
  - Open exact cited source chunks from the source-detail endpoint.

## Task 1: Document Governance API

- [x] Add tests that a bank admin can update document metadata and the update propagates to chunks.
- [x] Add tests that staff cannot update governance.
- [x] Add tests that one bank cannot update another bank's document.
- [x] Implement `PATCH /api/documents/{document_id}/governance`.
- [x] Implement a shared helper that updates chunk metadata and Qdrant payloads.
- [x] Commit: `Add document governance metadata endpoint`.

## Task 2: Document Lifecycle State API

- [x] Add tests for document lifecycle state transition.
- [x] Verify state transitions update `Document`, `DocumentChunk`, and Qdrant payload fields.
- [x] Implement `PATCH /api/documents/{document_id}/lifecycle`.
- [x] Commit: `Add document lifecycle governance endpoint`.

## Task 3: Bank-Scoped Source Viewer

- [x] Add tests that approved document chunks are visible to authorized same-bank users.
- [x] Add tests that draft global documents are hidden from staff.
- [x] Add tests that session uploads are only visible to the owner.
- [x] Add tests that cross-bank documents return 404.
- [x] Implement `GET /api/documents/{document_id}/source` with optional `page_number` and `chunk_index`.
- [x] Add chat evidence panel source-open flow.
- [x] Commit: `Add bank-scoped document source viewer`.

## Task 4: Appliance Health API

- [x] Add tests for healthy response shape.
- [x] Add tests that Redis/Qdrant failures are reported as degraded, not uncaught 500 errors.
- [x] Implement service checks for database, Qdrant, Redis queue length, disk usage, and document status counts.
- [x] Add `GET /api/analytics/appliance-health`.
- [x] Commit: `Add appliance health monitoring API`.

## Task 5: Monitoring Dashboard UI

- [x] Fetch `/analytics/appliance-health` from `frontend/src/pages/Analytics.jsx`.
- [x] Add compact cards for service health, queue depth, disk use, and document governance counts.
- [x] Show degraded services with amber/red status.
- [x] Keep existing Analytics layout and route.
- [x] Run frontend build.
- [x] Commit: `Show appliance health in analytics`.

## Task 6: Verification

- [x] Run `backend/.venv/bin/python -m pytest tests -q` from `backend/`.
- [x] Run frontend build.
- [ ] Verify `/health`, `/api/analytics/appliance-health`, and document source/governance endpoints locally or on the remote server after deploy.
- [ ] Push branch and deploy backend/frontend if requested.
