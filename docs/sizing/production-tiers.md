# LipiCore Production Sizing Tiers

This document defines conservative deployment tiers. These are capacity targets, not SLA claims, until load tests and restore drills are run and retained as evidence.

## Current Runtime Baseline

- Backend API: uvicorn with `WEB_CONCURRENCY`, default `2` workers.
- Ingestion worker: Redis/RQ queue with `INGESTION_WORKER_CONCURRENCY`, default `1`.
- Model serving: logical routes `LLM_A`, `LLM_B`, `LLM_C`, and `LLM_VISION`; effective capacity depends on the actual endpoints and GPUs.
- Per-user model limit: staff `1`, admin `2` by default.
- Model queue timeout: `LLM_QUEUE_TIMEOUT_SECONDS=120`; stale queue tokens are pruned by `LLM_QUEUE_STALE_SECONDS`.
- Upload limits: Document Library and chat uploads are sized for controlled pilots, not unlimited bulk ingestion.
- Chat context: route-specific context windows with prompt trimming.
- Retrieval: top candidates are reranked and a small source set is packed into the model prompt.
- Long-document analysis: queued Redis/RQ jobs with Tesseract OCR, direct parsers, excerpt packing, and deep-model generation.
- Internal workspace modules: feature-flagged employee search, notifications, CEO messages, market utilities, staff inbox, and workflow cases are mostly database/API workloads; workflow AI drafts still consume the configured model route when implemented through chat or model-backed flows.

## Evidence Required For Any Tier

- Load-test report for the claimed active user count.
- RAG evaluation gate on bank-approved documents.
- Policy citation evidence for heading, clause, PDF page, and printed page where available.
- Representative upload tests.
- Smoke tests for enabled internal workspace modules.
- Model health and queue evidence.
- Redis queue depth and worker failure review.
- Backup and restore evidence.
- Rollback procedure.

## Tier 1: Pilot

Use for one department or one controlled bank pilot.

- Target population: 25-75 named staff.
- Expected active users: 10-25.
- Backend workers: `WEB_CONCURRENCY=2`.
- Ingestion workers: `INGESTION_WORKER_CONCURRENCY=1`.
- Model serving: one text/deep model endpoint; optional fast or vision endpoint only after capacity testing.
- Storage: single PostgreSQL, Qdrant, Redis, and object storage with daily backups.
- Availability posture: not HA; planned maintenance acceptable.
- Proof required: 25-user load run, representative uploads, RAG gate, backup evidence.
- Long-document guidance: allow only a small number of concurrent heavy jobs until worker memory and model queue time are measured.
- Internal workspace guidance: enable only the modules included in the pilot scope; keep feature flags off for untrained teams.

## Tier 2: Department

Use for a real department rollout such as customer care, compliance, or credit operations.

- Target population: 100-500 named staff.
- Expected active users: 25-75.
- Backend workers: start at `WEB_CONCURRENCY=4`, then size after CPU and memory checks.
- Ingestion workers: start at `1`; raise to `2` only after upload/indexing tests show stable memory and embedding latency.
- Model serving: at least one text/analyst endpoint; add a separate fast route or replica only with benchmark evidence.
- Storage: backed-up PostgreSQL, Qdrant snapshots, Redis persistence, monitored disk growth.
- Operations: uptime monitoring, model health checks, queue-time dashboards, and weekly audit review.
- Proof required: 50-user load run plus representative document ingestion and RAG gate.
- Long-document guidance: test a queue of clean PDFs, scanned PDFs, and Excel workbooks before promising same-day bulk onboarding.
- Internal workspace guidance: identify operational owners for employee profile hygiene, notifications, CEO messages, and exchange-rate updates before enabling those modules for a department.

## Tier 3: Whole Bank

Use only after department-level measurements prove demand and capacity.

- Target population: 1,000+ named staff.
- Expected active users: 100+.
- Backend workers: horizontally scaled API containers behind nginx or a load balancer.
- Ingestion workers: separate worker pool with queue-depth alerts, failed-job review, and controlled concurrency per host.
- Model serving: multiple replicas or explicit queue/SLA limits; separate interactive and long-document capacity where needed.
- Storage: HA PostgreSQL, Qdrant replication/snapshots, Redis HA or accepted queue-loss policy, durable object storage.
- Operations: centralized logs, metrics, alerting, patch process, rollback process, and bank IT runbook.
- Proof required: 100-user or bank-agreed load test, ingestion stress test, backup restore test, model queue timeout evidence, and disaster recovery drill.
- Bank-readiness evidence: complete [../deployment/bank-readiness-checklist.md](../deployment/bank-readiness-checklist.md).
- Deployment reference: [../../deploy/ha/README.md](../../deploy/ha/README.md).
- Internal workspace guidance: size PostgreSQL storage and retention for notifications, work items, employee profiles, exchange-rate batches, workflow cases, and audit evidence.

## Known Limits To State Honestly

- Large files may upload but extraction, chunking, embedding, and indexing still take time.
- Uploads enqueue ingestion work; users should expect queued/processing states.
- Scanned PDFs, complex tables, merged cells, charts, handwriting, seals, and signatures need staff review.
- Heavy OCR, large PDF, and Excel analysis should use queued long-document jobs.
- Current architecture is not high availability by default.
- Capacity numbers must cite the exact test run, server profile, prompt set, and model settings used.
- Employee directory, notifications, CEO messages, and exchange-rate utilities do not prove AI model capacity; include them in API/database load tests separately from model benchmarks.
