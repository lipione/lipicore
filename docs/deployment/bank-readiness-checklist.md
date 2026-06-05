# Bank Readiness Checklist

Use this checklist before calling a LipiCore deployment bank-ready. It applies to demos, pilots, controlled production, and whole-bank rollout claims. Evidence should be retained with the release notes or deployment ticket.

## Blocking Gates

A deployment is not bank-ready if any item below is true:

- Staff-facing routes are not protected by TLS.
- Production secrets are missing, weak, default, or stored in Git.
- Admin ownership is unknown.
- Database migrations are not current.
- Model health checks fail.
- RAG evaluation fails on the bank's approved documents.
- Policy-like answers cannot cite required heading, clause, and PDF page metadata.
- Any cross-bank or cross-session data leak is observed.
- Enabled internal workspace modules expose another bank's employee, notification, rate, message, or work-item data.
- PostgreSQL backup or restore evidence is missing.
- Qdrant snapshot or restore plan is missing.
- Uploaded representative documents cannot be processed.
- Rollback path is unknown for the release.

## Required Evidence

| Area | Required Evidence |
| --- | --- |
| TLS | HTTPS returns a valid certificate for staff-facing routes. |
| Secrets | `.env` uses strong bank-specific secrets outside Git. |
| Admin | Named owner for super admin and bank admin accounts. |
| Migrations | `alembic upgrade head` completed successfully. |
| Model health | Active vLLM routes return `/v1/models`; `/api/chat/models/status` is acceptable. |
| RAG gate | Bank-specific evaluation set passes thresholds. |
| Upload coverage | PDF, scanned PDF, DOCX, XLSX, PPTX, TXT/CSV, and image upload tests completed. |
| Source evidence | Answers show expected document, document heading, clause, PDF page, printed page when available, section metadata, passage, and citation status. |
| Citation completeness | Policy-like answers missing required heading, clause, or PDF page return a citation-incomplete review response rather than final advice. |
| Long-document analysis | Clean PDF, scanned PDF, and Excel queued analysis jobs tested if the workflow is enabled. |
| OCR quality | Low-confidence or poor extraction cases are documented for staff review. |
| Feature controls | Super Admin has reviewed enabled/disabled state for every internal workspace feature. |
| Employee directory | Search, filtering, disabled-employee visibility, and cross-bank isolation tested if enabled. |
| Notifications and CEO messages | Publish, read, acknowledgement, expiry/audience behavior, and audit evidence tested if enabled. |
| Forex/time/date | Bank owner identified for rate updates; at least one rate batch published; 2-3 times/day update process documented if enabled. |
| Staff Inbox/workflows | Assignment, staff update, admin bank-wide listing, and feature-disabled behavior tested if enabled. |
| Queue health | Redis queue depth, failed jobs, worker logs, and job age reviewed. |
| GPU capacity | GPU memory and model queue status reviewed after representative use. |
| PostgreSQL | Backup within 24 hours and restore drill within 30 days for production claims. |
| MinIO/object storage | Backup within 24 hours or durable object-storage policy documented. |
| Qdrant | Snapshot within 7 days or equivalent vector-store restore policy documented. |
| Redis | Persistence enabled or accepted queue-loss policy documented. |
| Rollback | Rollback command or release revert procedure documented. |

## Demo Minimum

For a bank demo, complete at least:

1. TLS and login check.
2. Model health check.
3. Upload one approved knowledge PDF and one scanned/OCR sample.
4. Run a small evaluation set with at least one not-found case.
5. Ask a source-backed policy question and verify heading, clause, PDF page, printed page when available, and citation status in the evidence panel.
6. Smoke-test any enabled internal workspace page that will be shown.
7. Queue one long-document analysis job if that feature will be shown.

## Pilot Minimum

For a pilot, complete all demo items plus:

1. Representative document upload coverage.
2. Bank-specific RAG release gate.
3. Backup/restore evidence.
4. Queue and GPU capacity review.
5. Named support and admin owners.
6. Named owners for feature controls, employee directory data, notifications/CEO messages, and exchange-rate updates where those features are enabled.
7. Staff-facing limits and non-claims reviewed with the bank team.

## Whole-Bank Minimum

For whole-bank production, single-host Compose is not enough. Complete all pilot items plus:

1. HA PostgreSQL or managed equivalent.
2. Qdrant replication/snapshot/restore plan.
3. Redis HA or accepted queue-loss policy.
4. Durable object storage.
5. Backend/frontend replicas behind a load balancer.
6. Model redundancy or explicit capacity/SLA limits.
7. Centralized logs, metrics, and alerts.
8. Disaster recovery runbook and restore drill.
9. Load-test evidence matching the claimed user population.
10. Internal workspace data retention and ownership policy for employee profiles, notifications, CEO messages, work items, and exchange-rate batches.
