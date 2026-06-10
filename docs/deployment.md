# LipiCore Deployment And Operations

This guide covers pilot, staging, and controlled production deployments. It is the canonical deployment document; root-level deployment files point here to avoid duplicate stale instructions.

## Deployment Boundary

The repository's default deployment is a private Docker Compose stack with FastAPI, React/Vite, PostgreSQL, Qdrant, Redis, MinIO, nginx, an ingestion worker, messenger backend, internal workspace APIs, and local OpenAI-compatible vLLM endpoints.

Single-host Compose is suitable for pilots and controlled trials. Whole-bank production requires the HA guidance in [../deploy/ha/README.md](../deploy/ha/README.md), retained load-test evidence, backup/restore drills, monitoring, and rollback procedures.

## Prerequisites

- Linux host, typically Ubuntu 22.04 or 24.04 LTS.
- Docker Engine and Docker Compose v2.
- NVIDIA driver and NVIDIA container runtime when serving local GPU models.
- Model files available at the host paths expected by `docker-compose.yml` or deployment overrides.
- DNS and TLS plan for staff-facing access.
- Strong secrets in `.env`; no production secrets in Git.

## Important Environment Variables

| Variable | Purpose |
| --- | --- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` | PostgreSQL metadata database. |
| `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Authentication token configuration. |
| `AUTH_ACCOUNT_LOCKOUT_MAX_FAILURES`, `AUTH_ACCOUNT_LOCKOUT_WINDOW_MINUTES`, `RATE_LIMIT_STORAGE_URI` | Login lockout and shared rate-limit storage. Use Redis-backed storage in production. |
| `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION_NAME` | Vector database connection and collection. |
| `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` | Object storage for uploaded files. |
| `REDIS_URL` | Redis for RQ and model admission control. |
| `LLM_A_*`, `LLM_B_*`, `LLM_C_*` | Fast, secondary, and deep local model routes. |
| `LLM_VISION_*` | Optional document-image/vision route. |
| `LLM_*_MAX_CONCURRENCY`, `LLM_USER_MAX_CONCURRENCY`, `LLM_ADMIN_MAX_CONCURRENCY` | Admission-control limits. |
| `LLM_FAST_CONTEXT_WINDOW_TOKENS`, `LLM_DEEP_CONTEXT_WINDOW_TOKENS`, `LLM_VISION_CONTEXT_WINDOW_TOKENS` | Per-route context budgets. |
| `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `EMBEDDING_NORMALIZE` | Embedding model settings. |
| `INGESTION_QUEUE_NAME`, `INGESTION_JOB_TIMEOUT_SECONDS`, `INGESTION_WORKER_CONCURRENCY` | Worker queue behavior. |
| `OCR_ENGINE`, `OCR_LANGUAGES`, `OCR_MAX_PAGES`, `OCR_TEXT_LAYER_REPAIR_MAX_PAGES` | OCR behavior and limits. |
| `COOKIE_SECURE`, `ALLOWED_ORIGINS` | Browser security and CORS. |

Internal banking workspaces do not require separate environment variables in the current implementation. They are controlled through per-bank feature flags after migrations are applied.

## First-Time Setup

```bash
git clone <repo-url>
cd BankAi
cp .env.example .env
# edit .env with bank-specific secrets, model routes, allowed origins, and storage settings
./deploy/upgrade.sh
```

Run migrations:

```bash
docker compose exec backend alembic upgrade head
```

Check service health:

```bash
docker compose ps
./deploy/upgrade.sh --check-only
```

Expected local endpoints:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Qdrant: `http://localhost:6333`
- MinIO console: `http://localhost:9001`

## Compose Services

| Service | Role |
| --- | --- |
| `backend` | FastAPI app, auth, RAG, chat, documents, evaluations, analytics, audit, OCR extraction, long-document APIs. |
| `frontend` | React/Vite staff workspace. |
| `nginx` | Public reverse proxy for frontend, backend, and messenger routes. |
| `db` | PostgreSQL metadata and full-text search. |
| `qdrant` | Vector search and payload filtering. |
| `redis` | RQ queue and model admission-control state. |
| `minio` | Uploaded document object storage. |
| `ingestion-worker` | Extraction, OCR, chunking, embedding, Qdrant indexing, long-document analysis. |
| `messenger-backend` | Staff Messenger API and attachment handling. |
| `vllm-b` | Optional fast text route in the repository profile. |
| `vllm-c` | Deep/text model route in the repository profile. |
| `vllm-vision` | Optional vision/document-image route behind the Compose `vision` profile. |

## Upgrade Flow

Use the health-gated upgrade script for normal app releases:

```bash
./deploy/upgrade.sh
```

For a health-only check:

```bash
./deploy/upgrade.sh --check-only
```

For test/staging releases where backend tests should gate the upgrade:

```bash
./deploy/upgrade.sh --run-tests
```

If a release changes the schema:

```bash
docker compose exec backend alembic upgrade head
```

This release line includes feature-flag, employee profile, market utility, notification, CEO message, staff work item, governance workflow, banking workflow, and policy citation metadata migrations. Verify Alembic reports the latest head before enabling the new workspaces.

If a release changes embedding model, embedding dimension, or collection name, use a new Qdrant collection or rebuild the index:

```bash
docker compose exec backend python scripts/reindex_document_vectors.py
```

If existing approved policy-like documents were indexed before citation metadata fields existed, run citation backfill per document after migration:

```text
POST /api/documents/{document_id}/citation-backfill
```

Allowed backfill roles are `super_admin`, `bank_admin`, `compliance_officer`, and `document_reviewer`. The endpoint updates PostgreSQL chunks first and then updates scoped Qdrant payloads best-effort. Any Qdrant update errors are returned in `qdrant_update_errors` and should be retained with release evidence.

Enable optional employee-facing workspaces only after the bank confirms scope:

```text
GET /api/feature-flags?bank_id={bank_id}
PATCH /api/feature-flags/{bank_id}/{feature_key}
GET /api/feature-flags/effective
```

All new feature keys default to disabled. See [internal-banking-workspace.md](internal-banking-workspace.md).

## Model Routing Guardrails

The code supports multiple local model routes, but real capacity depends on the deployed GPUs and the active endpoints. Do not assume `LLM_A`, `LLM_B`, and `LLM_C` are independent just because the variables exist. If several routes point to the same vLLM server, size concurrency against that single server.

Before changing or restarting model services:

```bash
nvidia-smi
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep 'lipicore-vllm'
curl -s http://localhost:8002/v1/models || true
curl -s http://localhost:8003/v1/models || true
curl -s http://localhost:8007/v1/models || true
```

Restart GPU model services only inside a maintenance window.

## Operational Checks

General health:

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 nginx
docker compose logs --tail=100 redis
docker stats
```

Worker and long-document health:

```bash
docker compose logs --tail=200 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 backend
```

Model queue status:

```text
GET /api/chat/models/status
```

RAG evaluation:

```text
Frontend: /evaluations
API: POST /api/evaluations/rag
```

Bank readiness:

```text
Frontend: /analytics
API: GET /api/analytics/bank-readiness
```

Internal workspace checks:

```text
GET /api/feature-flags/effective
GET /api/employee-directory
GET /api/market-utilities/summary
GET /api/notifications/unread-count
GET /api/ceo-messages
GET /api/staff-work-items
```

Market-rate operations:

```text
POST /api/market-utilities/rate-batches
```

Rates are bank-published values, normally updated by Treasury or an authorized admin 2-3 times per business day. They are not live scraped market feeds. Record the source name, publish timestamp, and notes for each batch.

## TLS And Network Hardening

- Terminate TLS at nginx or an approved enterprise reverse proxy.
- Set `COOKIE_SECURE=true` in production.
- Restrict `ALLOWED_ORIGINS` to approved domains and explicit test origins.
- Expose only 80/443 and the operator SSH path publicly.
- Keep PostgreSQL, Qdrant, Redis, MinIO, backend debug ports, and vLLM ports private.
- Rotate default credentials before user testing.
- Keep TLS renewal monitored.

## Backup And Restore

Back up these together so document metadata and vector payloads stay consistent:

- PostgreSQL database.
- MinIO/object storage.
- Qdrant storage or snapshots.
- `.env`.
- nginx/TLS configuration.
- deployment overrides.

Example database backup:

```bash
mkdir -p /data/lipicore/backups
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > /data/lipicore/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

A bank-ready deployment needs restore evidence, not just backup files. See [deployment/bank-readiness-checklist.md](deployment/bank-readiness-checklist.md).

## Troubleshooting

### Backend Is Running But Not Healthy

```bash
docker compose logs --tail=200 backend
docker compose ps qdrant redis db
```

Common causes:

- database migrations not applied;
- Qdrant collection dimension mismatch;
- Redis unavailable;
- embedding model cache/path missing;
- bad `.env` secrets or invalid CORS/origin settings.

### vLLM Does Not Start

```bash
docker compose logs --tail=200 vllm-c
docker logs --tail=200 lipicore-vllm-vision
nvidia-smi
```

Common causes:

- model path missing or wrong;
- GPU already occupied;
- `max-model-len`, `max-num-seqs`, or GPU utilization too high;
- model name mismatch between served model and `LLM_*_MODEL`.

### Slow Or Queued Responses

```bash
docker compose logs --tail=100 backend
docker compose logs --tail=100 redis
```

Check `/api/chat/models/status`. If waiting requests stay high, lower token caps, lower concurrency, separate fast/deep model routes, or add GPU capacity.

### Long-Document Job Stuck Or Failed

```bash
docker compose logs --tail=200 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 backend
```

Common causes:

- worker is not running;
- migrations missing `long_document_analysis_job`;
- extraction produced no usable text;
- OCR dependencies unavailable;
- deep model queue timed out;
- file is too complex for current OCR/table extraction quality.

### File Upload Failures

```bash
docker compose logs --tail=100 backend
docker compose logs --tail=100 minio
df -h
```

Verify MinIO credentials, bucket existence, upload limits, and available disk.

### Citation-Incomplete Policy Answers

If policy answers return a citation-incomplete response:

- inspect the source panel for missing PDF page, heading, or clause metadata;
- confirm the source document type is correctly set as policy/procedure/circular/directive/SOP/law/act/compliance where appropriate;
- run citation backfill for older approved documents;
- inspect the document source viewer to confirm chunks include `document_heading`, `clause_number`, and `pdf_page_number`;
- re-run the bank-specific RAG evaluation gate after fixing ingestion or document metadata.

### Feature Disabled In Workspace

If a workspace page reports that a feature is disabled:

```text
GET /api/feature-flags/effective
```

Confirm the feature is enabled for that bank and that the user has the required role permission. Feature flags are intentionally separate from role permissions: both must allow access.

## Release Gate

Before returning a deployment to bank staff:

1. `docker compose ps` shows expected healthy app services.
2. Migrations are at head.
3. Backend tests and frontend lint/build pass in staging.
4. Representative uploads complete: PDF, scanned PDF, DOCX, XLSX, PPTX, TXT/CSV, and image.
5. Bank-specific RAG evaluation passes.
6. Policy-like answers show heading, clause, PDF page, printed page when available, and citation status; missing required citation fields are blocked.
7. Enabled internal workspace features pass a smoke test with bank-scoped data.
8. Bank-published exchange rates have an owner and update procedure if `market_time` is enabled.
9. Model health and queue status are acceptable.
10. Backups and restore evidence are current.
11. Rollback steps are known for the release.

Failures in source recall, citation terms, clause/page citation behavior, not-found behavior, cross-bank isolation, cross-session isolation, backup, restore, or model health are release blockers.
