# BankAi Public Deployment - Live

**Date:** May 23, 2026
**Status:** Production stack deployed at commit `615d299`; staff helpdesk, document governance, OCR extraction, Model Lab, and queued long-document analysis are live

## Public Access

```text
https://ai.silverlining.com.np
```

HTTP requests are redirected to HTTPS. The legacy IP entry point is not the primary
access URL.

## Current Architecture

```text
Users
  |
  v
nginx reverse proxy
  - port 80: redirect to HTTPS
  - port 443: TLS termination with Let's Encrypt
  |
  +-- frontend (internal port 3000)
  +-- backend API (internal port 8000)
        |
        +-- PostgreSQL
        +-- Qdrant vector database
        +-- MinIO object storage
        +-- Redis admission control and RQ queue
        +-- RQ ingestion and long-document analysis queue
        +-- vLLM text/analyst model on GPU 1
        +-- vLLM vision/OCR model on GPU 0
```

## Running Services

| Service | Container | Purpose | External Port |
|---------|-----------|---------|---------------|
| nginx | `lipicore-nginx` | HTTPS reverse proxy | 80, 443 |
| frontend | `lipicore-frontend` | React UI | proxied |
| backend | `lipicore-backend` | FastAPI API | proxied |
| PostgreSQL | `lipicore-db` | relational data | internal |
| Qdrant | `lipicore-qdrant` | vector search | internal |
| MinIO | `lipicore-minio` | document storage | internal |
| Redis | `lipicore-redis` | LLM request admission control | internal |
| ingestion worker | `lipicore-ingestion-worker` | document ingestion and queued long-document analysis | internal |
| vLLM text/analyst | `lipicore-vllm-c` | Gemma 4 26B 4-bit on GPU 1 | 8003 |
| vLLM vision/OCR | `lipicore-vllm-vision` | Qwen3-VL 8B on GPU 0 | 8007 |

`lipicore-vllm-b` is not running in the current production profile. Do not
start it unless a GPU capacity decision is made first.

## Model Runtime

The deployment uses vLLM only. Ollama and LoRA adapters are not part of the
current stack.

| Route | Container | Served model name | GPU | Current role |
|------|-----------|-------------------|-----|--------------|
| Text A/B/C | `lipicore-vllm-c` | `gemma-4-26b-4bit` | 1 | All interactive text, analyst, support, compliance, loan, and long-document generation |
| Vision | `lipicore-vllm-vision` | `qwen3-vl-8b` | 0 | Vision/OCR file analysis route |

The production `docker-compose.yml` and `.env` on `/data/bankai` intentionally
route `LLM_A`, `LLM_B`, and `LLM_C` to `lipicore-vllm-c`. This differs from the
repository default two-text-tier profile. Preserve the production files during
deployments.

Redis coordinates distributed queueing so the backend can reject or wait on
requests instead of overloading GPU memory.

Heavy OCR, large PDF, and Excel workbook analysis should be queued from Document
Library. The job uses the ingestion worker plus the text/analyst model, stores
progress and results in PostgreSQL, and should be monitored separately from
interactive chat latency.

## TLS Status

Let's Encrypt certificate:

```text
Domain: ai.silverlining.com.np
Issuer: Let's Encrypt E7
Expires: 2026-08-05
```

nginx mounts the certificate directory from:

```text
/data/bankai/letsencrypt
```

Renewal should be scheduled before the expiry date, followed by an nginx reload.

## Verification Commands

Run these on the remote server from `/data/bankai`:

```bash
docker compose ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep 'lipicore-vllm'
curl -I http://ai.silverlining.com.np
curl -I https://ai.silverlining.com.np
curl -s http://localhost:8003/v1/models
curl -s http://localhost:8007/v1/models
curl -fsS http://127.0.0.1:8000/health
curl -I http://127.0.0.1:3000/
nvidia-smi
docker compose logs --tail=100 backend
docker compose logs --tail=100 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 vllm-c
```

Authenticated operators can also check model admission state through:

```text
GET /api/chat/models/status
```

Long-document job status is available through authenticated API calls:

```text
GET /api/long-document-analysis
```

Protected routes such as `/api/model-lab/status` and
`/api/long-document-analysis` should return `401` without an authenticated
session.

## Operator Notes

- Do not publish admin passwords or JWT secrets in documentation.
- Manage credentials through the remote `.env` file or a secret manager.
- Use `https://ai.silverlining.com.np` for browser testing.
- Chat UI now supports a mobile drawer layout, corrected model labels for the
  current vLLM routes, safer uploaded-document source selection, real message
  timestamps, and env-driven Playwright checks.
- Current deployed workflows include staff chat, approved knowledge, Document
  Library, OCR Extraction, Compliance Workspace, Model Lab, and queued
  long-document analysis.
- App-only deploys should rebuild/recreate backend, frontend, messenger backend,
  ingestion worker, and nginx with `--no-deps`. Do not restart GPU model
  containers without a maintenance window and capacity check.
- If Chrome still labels the site "Not secure" while the certificate is valid,
  clear site data/HSTS state or retest in a fresh Incognito window. Public TLS
  verification and headless browser checks passed for the current certificate.

## Remote Server Details

```text
IP: 202.51.2.50
SSH port: 41447
Deployment path: /data/bankai
User: ekduiteen
Deployed commit: 615d299
Pre-deploy backup: /data/bankai-backups/20260521-151613-pre-615d299
```
