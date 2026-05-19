# Phase 2A Ingestion Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move document ingestion out of FastAPI background tasks into a Redis-backed worker queue with explicit worker concurrency limits.

**Architecture:** Upload endpoints create the document record, mark it as queued, and enqueue `process_document(document_id)` into Redis/RQ. A separate `ingestion-worker` container consumes the queue, so API workers remain responsive while extraction, chunking, embedding, indexing, summary generation, and cataloging run outside the request path.

**Tech Stack:** FastAPI, SQLModel, Redis, RQ, Docker Compose, existing ingestion service.

---

### Task 1: Queue Service

**Files:**
- Create: `backend/app/services/ingestion_queue.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_ingestion_queue.py`

- [x] Add ingestion queue settings for queue name, timeout, retry count, and worker concurrency.
- [x] Add `rq` dependency.
- [x] Add `enqueue_document_ingestion(document_id, db)` that marks the document queued and enqueues the ingestion job.
- [x] Add a unit test proving the document is marked queued and the job is sent to the queue.

### Task 2: API Integration

**Files:**
- Modify: `backend/app/api/documents.py`
- Modify: `backend/app/api/chat.py`

- [x] Remove FastAPI `BackgroundTasks` ingestion calls from document uploads.
- [x] Enqueue document ingestion through the new queue service.
- [x] Return queued status for session uploads.
- [x] Surface queue failures as `503` instead of silently pretending ingestion started.

### Task 3: Worker Process

**Files:**
- Create: `backend/app/workers/__init__.py`
- Create: `backend/app/workers/ingestion_worker.py`
- Modify: `docker-compose.yml`

- [x] Add an RQ worker entrypoint.
- [x] Support `INGESTION_WORKER_CONCURRENCY`, defaulting to `1`.
- [x] Add an `ingestion-worker` service to Docker Compose with the same backend runtime environment.

### Task 4: Verification And Docs

**Files:**
- Modify: `docs/sizing/production-tiers.md`
- Modify: `docs/deployment.md`

- [x] Document the queue and worker sizing defaults.
- [x] Run syntax verification for touched Python files.
- [x] Run `docker compose config`.
- [x] Run targeted tests where local dependencies allow it.
