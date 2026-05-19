# BankAi Enterprise Deployment Guide

**Version:** 1.2
**Date:** May 19, 2026
**For:** On-premises or private data center deployment

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16+ cores |
| RAM | 64 GB | 128+ GB |
| Storage | 500 GB SSD | 1 TB+ SSD/NVMe |
| GPU | 2 NVIDIA GPUs | separate GPUs for fast and deep tiers |
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
        +-- vLLM fast tier on GPU 0
        +-- vLLM deep tier on GPU 1
```

The current production deployment uses clean Gemma 4 models with no LoRA
adapters and no Ollama service.

## Pre-Deployment Checklist

1. DNS points to the server public IP.
2. Ports 80 and 443 are open to the internet.
3. SSH is restricted to the operator port or private network.
4. `/data/bankai` exists and is owned by the deployment user.
5. Gemma model directories exist on the host:
   - `/data/models/llm/gemma-4-E4B-it`
   - `/data/models/llm/gemma-4-26b-a4b-awq-4bit`
6. `.env` contains production secrets and public origins.

## Installation

```bash
cd /data/bankai
cp .env.example .env
nano .env
docker compose up -d --build
docker compose ps
```

Run database migrations if the release includes schema changes:

```bash
docker compose exec backend alembic upgrade head
```

Create or rotate admin users through the application admin flow or a one-time
operator script. Do not commit passwords or JWT secrets to Git.

## vLLM Runtime

Fast tier:

```text
Container: lipicore-vllm-b
Served name: gemma-4
Model path: /data/models/llm/gemma-4-E4B-it
GPU: 0
External debug port: 8002
```

Deep tier:

```text
Container: lipicore-vllm-c
Served name: gemma-4-26b-4bit
Model path: /data/models/llm/gemma-4-26b-a4b-awq-4bit
GPU: 1
External debug port: 8003
```

Verify the model servers:

```bash
curl -s http://localhost:8002/v1/models
curl -s http://localhost:8003/v1/models
docker compose logs --tail=100 vllm-b
docker compose logs --tail=100 vllm-c
```

## Redis Admission Control

Redis is used by the backend to coordinate model concurrency across requests.
The important settings are:

```text
REDIS_URL=redis://redis:6379/0
LLM_A_MAX_CONCURRENCY=12
LLM_C_MAX_CONCURRENCY=4
LLM_USER_MAX_CONCURRENCY=1
LLM_ADMIN_MAX_CONCURRENCY=2
LLM_QUEUE_TIMEOUT_SECONDS=120
LLM_FAST_MAX_TOKENS=512
LLM_DEEP_MAX_TOKENS=768
```

Authenticated operators can check queue state through:

```text
GET /api/chat/models/status
```

If Redis is temporarily unavailable, the backend falls back to in-process
admission control. That fallback is only suitable for a single backend replica.

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
docker compose restart vllm-b
docker compose restart vllm-c
docker compose restart nginx
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
docker compose logs --tail=200 vllm-b
docker compose logs --tail=200 vllm-c
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
| 1.2 | 2026-05-19 | Redis/RQ ingestion worker, document lifecycle and chunk permissions, reranking, citation verification, Evaluation Center, source evidence UI, health-gated upgrades |
| 1.1 | 2026-05-07 | vLLM two-GPU runtime, Redis admission control, Let's Encrypt HTTPS |
| 1.0 | 2026-04-28 | Initial enterprise deployment guide |
