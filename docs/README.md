# LipiCore Documentation

This directory is the canonical documentation set for LipiCore. Root-level architecture and deployment files intentionally point back here to avoid stale duplicate instructions.

## Read This First

- [Architecture](architecture.md): system components, request flow, ingestion, retrieval, memory, chunking, security boundaries, and current limits.
- [Deployment and operations](deployment.md): environment setup, Compose services, migrations, model routing, upgrades, backups, troubleshooting, and production guardrails.
- [Security architecture](security.md): isolation, RBAC, prompt-injection handling, source trust, audit, and operational hardening.
- [Internal banking workspace](internal-banking-workspace.md): feature flags, employee search, CEO messages, notifications, forex/time/date utilities, Staff Inbox, and banking workflow helpers.
- [Long-document analysis](long-document-analysis.md): queued large-file analysis workflow, API, access rules, limits, and monitoring.
- [RAG evaluations](evaluations/README.md): evaluation payloads, release gates, thresholds, seed packs, and failure handling.
- [Bank readiness checklist](deployment/bank-readiness-checklist.md): evidence required before demos, pilots, or production claims.
- [Production sizing tiers](sizing/production-tiers.md): pilot, department, and whole-bank capacity guidance.
- [Model capacity runbook](sizing/model-capacity-runbook.md): model-route and GPU-capacity checks.
- [HA reference](../deploy/ha/README.md): high-availability planning for production banking deployments.

## Product Docs And Proposals

Proposal and bank-facing collateral live under [proposals](proposals/). They are intentionally separate from engineering docs because they may be customized per bank, prepared date, pricing model, deployment profile, and sales context.

## Current Product Boundary

LipiCore is a bank staff-assistance and document-intelligence system. It can search approved knowledge, summarize and compare files, draft staff-facing content, run OCR extraction, queue long-document analysis, and expose evidence for review. It does not make final lending, compliance, regulatory, operational, or customer-impact decisions.

The internal banking workspace adds optional day-to-day employee tools around the assistant: Employee Search, Staff Inbox, CEO's Message, Notifications & Alerts, Forex/Time/Dates, knowledge-gap tracking, policy-change watch, audit evidence packs, and workflow helpers. These features are off by default and must be enabled per bank by Super Admin feature controls.

## Key Runtime Defaults

| Area | Default |
| --- | --- |
| Embedding model | `BAAI/bge-m3` |
| Embedding dimension | `1024` |
| Qdrant collection | `bank_documents_bge_m3` |
| Default chunk profile | 1000 chars / 200 overlap |
| Regulatory chunk profile | 900 chars / 180 overlap |
| OCR chunk profile | 800 chars / 100 overlap |
| Spreadsheet chunk profile | 1600 chars / 120 overlap |
| Presentation chunk profile | 900 chars / 120 overlap |
| Retrieval candidate limit | 24 before reranking |
| Context chunks | 5 max by default |
| Minimum source relevance | 0.4 |
| OCR fallback cap | `OCR_MAX_PAGES=200` |
| Long-document job timeout | `INGESTION_JOB_TIMEOUT_SECONDS=1800` |
| Default ingestion concurrency | `INGESTION_WORKER_CONCURRENCY=1` |
| Policy citation required fields | PDF page, document heading, clause number |
| Optional citation field | Printed page number |
| New workspace feature flags | Off by default per bank |

These defaults are implementation settings, not quality guarantees. Change them only with evaluation evidence and a vector-index migration plan where needed.

## Documentation Update Rules

- Update [architecture.md](architecture.md) when service boundaries, retrieval, model routing, memory, chunking, or trust behavior changes.
- Update [deployment.md](deployment.md) when Compose services, environment variables, migrations, health checks, or model endpoints change.
- Update [security.md](security.md) when roles, access checks, source trust, prompt handling, secrets, or audit behavior changes.
- Update [internal-banking-workspace.md](internal-banking-workspace.md) when feature keys, workspace routes, internal workflow APIs, or market-rate operating rules change.
- Update [evaluations/README.md](evaluations/README.md) when evaluator inputs, thresholds, seed packs, or release gates change.
- Update [deployment/bank-readiness-checklist.md](deployment/bank-readiness-checklist.md) when readiness evidence changes.

Avoid embedding a single live server's commit, domain, or model override in evergreen docs unless the doc is explicitly a dated deployment report.
