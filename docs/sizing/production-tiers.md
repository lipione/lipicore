# BankAi Production Sizing Tiers

This document defines conservative deployment tiers. These are capacity targets, not SLA claims, until load tests are run and retained as evidence.

## Current Runtime Baseline

- Backend API: uvicorn with `WEB_CONCURRENCY`, default `2` workers.
- Ingestion worker: Redis/RQ queue with `INGESTION_WORKER_CONCURRENCY`, default `1`.
- Current production text route: `LLM_A`, `LLM_B`, and `LLM_C` all share the Gemma 4 26B endpoint, so effective capacity is bounded by one text GPU.
- Repository capacity profile: fast model route `LLM_A_MAX_CONCURRENCY=12` and deep model route `LLM_C_MAX_CONCURRENCY=4` may be used only when separate endpoints are actually running.
- Per-user model limit: staff `1`, admin `2`.
- Model queue timeout: `LLM_QUEUE_TIMEOUT_SECONDS=120`; stale queue tokens are pruned after `LLM_QUEUE_STALE_SECONDS=10`.
- Upload limits: Document Library `50 MB`, AI Tasks `20 MB`.
- Chat context: 8192-token model context, with RAG top chunks kept intentionally small.
- Queued long-document analysis: uses Redis/RQ, open-source Tesseract OCR for scanned pages, plus the deep/analyst model for generated analysis; default OCR cap `OCR_MAX_PAGES=200`, legacy Nepali text-layer repair cap `OCR_TEXT_LAYER_REPAIR_MAX_PAGES=500`, job timeout `INGESTION_JOB_TIMEOUT_SECONDS=1800`, and deep context `LLM_DEEP_CONTEXT_WINDOW_TOKENS=8192`.

## Measured Test-Server Evidence

These numbers were measured on the current remote test server, not on every future bank appliance.

- 100 active staff API smoke: 2,357 requests, 0 failures, aggregate p95 57 ms.
- 20 separate staff streaming burst: 20/20 real answers, p50 8.41 s, p95 29.95 s, max 35.75 s.
- 40 separate staff streaming burst after queue-stale pruning: 40/40 real answers, p50 30.61 s, p95 80.19 s, max 86.76 s.
- One-user multi-stream tests are intentionally constrained by `LLM_USER_MAX_CONCURRENCY=1` and must not be used as whole-bank capacity evidence.

## Tier 1: Pilot

Use for one department or one controlled bank pilot.

- Target population: 25-75 named staff.
- Expected active users: 10-25.
- Backend workers: `WEB_CONCURRENCY=2`.
- Ingestion workers: `INGESTION_WORKER_CONCURRENCY=1`.
- Model serving: one text vLLM GPU; optional separate fast route only after capacity testing.
- Storage: single Postgres, Qdrant, Redis, and object/file storage with daily backups.
- Availability posture: not HA; planned maintenance acceptable.
- Proof required: 25-user Locust run with low API error rate and acceptable chat latency.
- Long-document guidance: allow only a small number of concurrent heavy OCR/PDF/XLS jobs until worker memory and analyst-model queue time are measured.
- Current evidence: 20 separate streaming staff completed with no failures on the test server.

## Tier 2: Department

Use for a real department rollout such as customer care, compliance, or credit operations.

- Target population: 100-500 named staff.
- Expected active users: 25-75.
- Backend workers: `WEB_CONCURRENCY=4`, sized after CPU and memory checks.
- Ingestion workers: start at `INGESTION_WORKER_CONCURRENCY=1`; raise to `2` only after upload/indexing tests show stable memory and embedding latency.
- Model serving: at least one text/analyst endpoint and, when capacity requires it, a separate fast-model replica. Add another text route if p95 latency or queue timeout is high.
- Storage: backed-up Postgres, Qdrant snapshots, Redis persistence, monitored disk growth.
- Operations: uptime monitoring, model health checks, queue-time dashboards, and weekly audit review.
- Proof required: 50-user Locust run plus representative document ingestion test.
- Long-document guidance: test a representative queue of clean PDFs, scanned PDFs, and Excel workbooks before promising same-day bulk onboarding.
- Current evidence: 100 active staff API smoke completed with no failures; 40 simultaneous streaming staff completed but with slow tail latency.

## Tier 3: Whole Bank

Use only after department-level measurements prove demand and capacity.

- Target population: 1,000+ named staff.
- Expected active users: 100+.
- Backend workers: horizontally scaled backend containers behind nginx or a load balancer.
- Ingestion workers: separate worker pool with queue-depth alerts, failed-job review, and controlled concurrency per host.
- Model serving: multiple fast-model replicas where enabled, analyst-model replicas separated by queue policy, and GPU-level monitoring.
- Storage: HA Postgres, Qdrant replication/snapshots, Redis HA, backup restore tests, and disaster recovery runbooks.
- Operations: centralized logs, metrics, alerting, patch process, rollback process, and bank IT runbook.
- Proof required: 100-user Locust run, ingestion stress test, backup restore test, and model queue timeout evidence.
- Long-document guidance: use a separate worker pool, queue-depth alerting, and analyst-model capacity policy so heavy analysis does not starve interactive staff chat.
- Deployment reference: `deploy/ha/README.md`.
- Current gap: whole-bank streaming concurrency has not been proven. More fast-model replicas or stricter queue policy are required before claiming instant AI for 100+ simultaneous staff.

## Known Limits To State Honestly

- Large files may upload but extraction, chunking, embedding, and indexing still take time.
- Uploads now enqueue ingestion work; users should expect queued/processing states instead of instant indexing.
- Scanned PDFs, complex tables, merged cells, charts, handwriting, seals, and signatures need stronger OCR/table extraction work before strong claims.
- Heavy OCR, large PDF, and Excel analysis should use queued long-document jobs. The workflow is safer than sending oversized text directly to chat, but it still depends on extraction quality and analyst-model capacity.
- Current architecture is not high availability by default.
- Capacity numbers must cite the specific `tests/load` run, server profile, and model settings used.
