# BankAi Enterprise Deployment Guide

**Version:** 1.4
**Date:** May 23, 2026
**For:** On-premises or private data center deployment

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16+ cores |
| RAM | 64 GB | 128+ GB |
| Storage | 500 GB SSD | 1 TB+ SSD/NVMe |
| GPU | 2 NVIDIA GPUs | separate GPUs for text/analyst and vision or optional fast tiers |
| Network | 1 Gbps | private network plus public 80/443 |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04/24.04 LTS |

Required software:

- Docker Engine 20.10+
- Docker Compose v2+
- NVIDIA driver and NVIDIA container runtime
- Git

## Target Architecture

```text
nginx 80/443
  +-- frontend
  +-- backend
        +-- PostgreSQL
        +-- Qdrant
        +-- MinIO
        +-- Redis
        +-- vLLM text model route
        +-- vLLM vision/OCR model route where enabled
```

The current production deployment uses clean Gemma 4 for text, Qwen3-VL for
vision/OCR, no LoRA adapters, and no Ollama service.

## Current Remote Production Profile

The live `/data/bankai` server is deployed at commit `615d299` with this
production override:

- `LLM_A_API_BASE`, `LLM_B_API_BASE`, and `LLM_C_API_BASE` all point to
  `http://lipicore-vllm-c:8000`.
- `LLM_A_MODEL`, `LLM_B_MODEL`, and `LLM_C_MODEL` all use
  `gemma-4-26b-4bit`.
- Vision/OCR uses `http://lipicore-vllm-vision:8000` with `qwen3-vl-8b`.
- `lipicore-vllm-b` is not running on the current server profile.

Preserve the production `docker-compose.yml`, `.env`, nginx config, TLS
directories, and running GPU containers during app-only deployments.

## Pre-Deployment Checklist

1. DNS points to the server public IP.
2. Ports 80 and 443 are open to the internet.
3. SSH is restricted to the operator port or private network.
4. `/data/bankai` exists and is owned by the deployment user.
5. Required model directories exist on the host for the selected profile:
   - `/data/models/llm/gemma-4-26b-a4b-awq-4bit`
   - Qwen3-VL weights or cache for the configured vision endpoint
   - `/data/models/llm/gemma-4-E4B-it` only if the fast 4B route is enabled
6. `.env` contains production secrets and public origins.

## Installation

For a fresh non-production install:

```bash
cd /data/bankai
cp .env.example .env
nano .env
docker compose up -d --build
docker compose ps
```

For the current production server, use an app-only deployment so GPU model
containers are not restarted accidentally:

```bash
cd /data/bankai
mkdir -p /data/bankai-backups/$(date +%Y%m%d-%H%M%S)-pre-upgrade
# Back up .env, docker-compose.yml, nginx.conf, letsencrypt, and certbot-lib.
git fetch --all --prune
git checkout <approved-commit>
# Restore production .env, docker-compose.yml, nginx.conf, and TLS directories.
docker compose build backend frontend messenger-backend ingestion-worker
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend frontend messenger-backend ingestion-worker nginx
docker compose ps
```

Do not run a blind `docker compose up -d --build` on the live server if it
would start, replace, or restart GPU model services.

Run database migrations if the release includes schema changes:

```bash
docker compose exec backend alembic upgrade head
```

Create or rotate admin users through the application admin flow or a one-time
operator script. Do not commit passwords or JWT secrets to Git.

## vLLM Runtime

Current production text route:

```text
Container: lipicore-vllm-c
Served name: gemma-4-26b-4bit
Model path: /data/models/llm/gemma-4-26b-a4b-awq-4bit
GPU: 1
External debug port: 8003
Routes: LLM_A, LLM_B, LLM_C
```

Current production vision/OCR route:

```text
Container: lipicore-vllm-vision
Served name: qwen3-vl-8b
GPU: 0
External debug port: 8007
```

Optional fast tier for future capacity work:

```text
Container: lipicore-vllm-b
Served name: gemma-4
Model path: /data/models/llm/gemma-4-E4B-it
External debug port: 8002
Status on current production server: not running
```

Verify the model servers:

```bash
curl -s http://localhost:8003/v1/models
curl -s http://localhost:8007/v1/models
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep 'lipicore-vllm'
docker compose logs --tail=100 vllm-c
nvidia-smi
```

## Redis Admission Control

Redis is used by the backend to coordinate model concurrency across requests.
Redis is also used by RQ for ingestion and queued long-document analysis. The important settings are:

```text
REDIS_URL=redis://redis:6379/0
INGESTION_QUEUE_NAME=document-ingestion
INGESTION_JOB_TIMEOUT_SECONDS=1800
INGESTION_WORKER_CONCURRENCY=1
OCR_MAX_PAGES=200
OCR_TEXT_LAYER_REPAIR_MAX_PAGES=500
OCR_VISION_REVIEW_MAX_PAGES=3
LLM_A_MAX_CONCURRENCY=12
LLM_C_MAX_CONCURRENCY=4
LLM_USER_MAX_CONCURRENCY=1
LLM_ADMIN_MAX_CONCURRENCY=2
LLM_QUEUE_TIMEOUT_SECONDS=120
LLM_FAST_MAX_TOKENS=512
LLM_DEEP_MAX_TOKENS=768
LLM_DEEP_CONTEXT_WINDOW_TOKENS=8192
```

If `LLM_A`, `LLM_B`, and `LLM_C` all point to the same 26B endpoint, size the
combined concurrency against that single GPU. Do not add the A/B/C limits
together as independent capacity.

Authenticated operators can check queue state through:

```text
GET /api/chat/models/status
```

If Redis is temporarily unavailable, the backend falls back to in-process
admission control. That fallback is only suitable for a single backend replica.

## Queued Long-Document Analysis

Large PDFs, OCR-heavy documents, and detailed Excel workbook review run as background jobs instead of blocking staff chat.

Operator checks:

```bash
docker compose logs --tail=100 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 backend
```

Before enabling this for a bank pilot, run migrations and test one clean PDF, one scanned PDF, and one Excel workbook:

```bash
docker compose exec backend alembic upgrade head
```

Monitor worker memory, Redis queue depth, job age, analyst-model queue time, and GPU memory before raising `INGESTION_WORKER_CONCURRENCY`.

## HTTPS Setup

The current production domain is:

```text
https://ai.silverlining.com.np
```

Issue a Let's Encrypt certificate from the deployment directory:

```bash
docker compose stop nginx
mkdir -p letsencrypt certbot-lib
docker run --rm -p 80:80 \
  -v /data/bankai/letsencrypt:/etc/letsencrypt \
  -v /data/bankai/certbot-lib:/var/lib/letsencrypt \
  certbot/certbot certonly --standalone \
  -d ai.silverlining.com.np \
  --non-interactive --agree-tos --register-unsafely-without-email
docker compose up -d nginx
```

nginx expects:

```text
/etc/letsencrypt/live/ai.silverlining.com.np/fullchain.pem
/etc/letsencrypt/live/ai.silverlining.com.np/privkey.pem
```

Verify TLS from a public machine:

```bash
curl -I http://ai.silverlining.com.np
curl -I https://ai.silverlining.com.np
```

Expected result: HTTP returns `301` to HTTPS and HTTPS returns `200`.

Schedule renewal before expiry:

```bash
docker run --rm -p 80:80 \
  -v /data/bankai/letsencrypt:/etc/letsencrypt \
  -v /data/bankai/certbot-lib:/var/lib/letsencrypt \
  certbot/certbot renew --standalone
docker compose restart nginx
```

## Operations

```bash
cd /data/bankai
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 nginx
docker compose logs --tail=100 redis
docker stats
```

Restart individual services:

```bash
docker compose restart backend
docker compose restart nginx
```

Restart model services only inside a maintenance window after confirming GPU
memory, driver/library health, and the exact production model profile:

```bash
nvidia-smi
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep 'lipicore-vllm'
docker compose restart vllm-c
```

Rebuild after code changes:

```bash
./deploy/upgrade.sh
```

For a health-only verification without rebuilding:

```bash
./deploy/upgrade.sh --check-only
```

When running on the server, the script checks the internal backend health URL
by default. If you run it from a host that can reach the public domain, add:

```bash
./deploy/upgrade.sh --check-only --public-health-url https://ai.silverlining.com.np/health
```

For the test server, run backend tests as part of the upgrade gate:

```bash
./deploy/upgrade.sh --run-tests
```

After release upgrades that affect RAG, ingestion, prompts, embeddings, or model routing, run a bank-specific evaluation set:

```text
Frontend: /evaluations
API: POST /api/evaluations/rag
```

Treat failures in expected sources, citation terms, or not-found behavior as release blockers for the affected workflow.

When changing `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, or `QDRANT_COLLECTION_NAME`, rebuild the vector index after the app starts:

```bash
docker compose exec backend python scripts/reindex_document_vectors.py
```

The current multilingual default is `BAAI/bge-m3`, `EMBEDDING_DIMENSION=1024`, and `QDRANT_COLLECTION_NAME=bank_documents_bge_m3`.

The production nginx config uses Docker's embedded DNS resolver for backend
and frontend upstreams. After backend or frontend containers are recreated,
nginx should resolve the new container IP automatically; verify with:

```bash
curl -fsS https://ai.silverlining.com.np/health
```

The Compose file also defines health checks for Redis, backend, frontend, and
nginx. Treat `running` as insufficient during an upgrade; the backend must show
`healthy` before frontend/nginx readiness means anything. A temporarily
`starting` backend is expected while it initializes Qdrant, seeds admin data,
and warms the embedding model.

## Troubleshooting

### Browser Still Shows "Not Secure"

Check the public certificate first:

```bash
curl -Iv https://ai.silverlining.com.np
```

If the certificate is valid and the browser still warns, clear site data/HSTS
state or retest in Incognito. Chrome can keep stale security state after a site
switches from self-signed TLS to Let's Encrypt.

### vLLM Does Not Start

```bash
docker compose logs --tail=200 vllm-c
docker logs --tail=200 lipicore-vllm-vision
nvidia-smi
```

Common causes:

- Model path missing or mounted incorrectly.
- GPU already occupied by another service.
- `max-model-len`, `max-num-seqs`, or GPU utilization too high for the card.
- Deep model requires enough `max-num-batched-tokens` for multimodal metadata.

### Slow or Queued Responses

```bash
docker compose logs --tail=100 backend
docker compose logs --tail=100 redis
```

Check `/api/chat/models/status` with an authenticated session. If `waiting`
stays high, reduce per-request token caps, lower UI concurrency, or add more GPU
capacity.

### Long-Document Job Stuck Or Failed

```bash
docker compose logs --tail=200 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 backend
```

Common causes:

- Worker is not running or cannot reach Redis.
- `long_document_analysis_job` table is missing because migrations were not run.
- File extraction failed or produced no text.
- OCR dependencies or the vision endpoint are unavailable.
- Deep model queue timed out under load.
- File is too complex for current OCR/table extraction quality.

### File Upload Failures

```bash
docker compose logs --tail=100 backend
docker compose logs --tail=100 minio
df -h /data/bankai
```

Verify MinIO credentials in `.env` and confirm the document bucket exists.

### Database Issues

```bash
docker compose ps db
docker compose logs --tail=100 db
docker compose exec db psql -U postgres -d bankai
```

## Security Hardening

- Keep only 80, 443, and the SSH operator port exposed publicly.
- Do not expose PostgreSQL, Qdrant, MinIO, Redis, or backend debug ports outside
  trusted networks.
- Set `COOKIE_SECURE=true` in production.
- Restrict `ALLOWED_ORIGINS` to the production domain and explicit test origins.
- Rotate default credentials before sharing the system with testers.
- Keep TLS certificates renewed and monitor expiry.
- Keep model debug ports firewalled unless they are needed for operator checks.

## Backup

Back up at minimum:

- PostgreSQL database
- MinIO data
- Qdrant storage
- `.env`
- `nginx.conf`
- `letsencrypt`

Example database backup:

```bash
mkdir -p /data/bankai/backups
docker compose exec -T db pg_dump -U postgres bankai \
  > /data/bankai/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

For a full host restore, recover data volumes and configuration first, then run:

```bash
cd /data/bankai
docker compose up -d --build
docker compose ps
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4 | 2026-05-23 | Current production profile, app-only deployment guidance, text route consolidation on `vllm-c`, Qwen3-VL vision endpoint, and GPU restart guardrails |
| 1.3 | 2026-05-21 | Queued long-document analysis for heavy OCR/PDF/XLS jobs, stored results, role-scoped job access, and worker/analyst-model operating guidance |
| 1.2 | 2026-05-19 | Redis/RQ ingestion worker, document lifecycle and chunk permissions, reranking, citation verification, Evaluation Center, source evidence UI, health-gated upgrades |
| 1.1 | 2026-05-07 | vLLM two-GPU runtime, Redis admission control, Let's Encrypt HTTPS |
| 1.0 | 2026-04-28 | Initial enterprise deployment guide |
