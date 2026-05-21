# BankAi Public Deployment - Live

**Date:** May 21, 2026
**Status:** Production stack deployed; queued long-document analysis documented for rollout

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
        +-- Redis admission control
        +-- RQ ingestion and long-document analysis queue
        +-- vLLM fast model on GPU 0
        +-- vLLM deep model on GPU 1
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
| ingestion worker | `ingestion-worker` | document ingestion and queued long-document analysis | internal |
| vLLM fast | `lipicore-vllm-b` | clean Gemma 4 4B on GPU 0 | 8002 |
| vLLM deep | `lipicore-vllm-c` | clean Gemma 4 26B 4-bit on GPU 1 | 8003 |

## Model Runtime

The deployment uses vLLM only. Ollama and LoRA adapters are not part of the
current stack.

| Tier | Served model name | Model path | GPU | Capacity target |
|------|-------------------|------------|-----|-----------------|
| Fast | `gemma-4` | `/data/models/llm/gemma-4-E4B-it` | 0 | 12 concurrent generations |
| Deep | `gemma-4-26b-4bit` | `/data/models/llm/gemma-4-26b-a4b-awq-4bit` | 1 | 4 concurrent generations |

The backend routes normal chat work to the fast tier and deep/file-analysis work
to the 26B tier. Redis coordinates distributed queueing so the backend can reject
or wait on requests instead of overloading GPU memory.

Heavy OCR, large PDF, and Excel workbook analysis should be queued from Document
Library. The job uses the ingestion worker plus the deep model, stores progress
and results in PostgreSQL, and should be monitored separately from interactive
chat latency.

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
curl -I http://ai.silverlining.com.np
curl -I https://ai.silverlining.com.np
curl -s http://localhost:8002/v1/models
curl -s http://localhost:8003/v1/models
docker compose logs --tail=100 backend
docker compose logs --tail=100 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 vllm-b
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

## Operator Notes

- Do not publish admin passwords or JWT secrets in documentation.
- Manage credentials through the remote `.env` file or a secret manager.
- Use `https://ai.silverlining.com.np` for browser testing.
- Chat UI now supports a mobile drawer layout, corrected model labels for clean
  Gemma 4 vLLM tiers, safer uploaded-document source selection, real message
  timestamps, and env-driven Playwright checks.
- If Chrome still labels the site "Not secure" while the certificate is valid,
  clear site data/HSTS state or retest in a fresh Incognito window. Public TLS
  verification and headless browser checks passed for the current certificate.

## Remote Server Details

```text
IP: 202.51.2.50
SSH port: 41447
Deployment path: /data/bankai
User: ekduiteen
```
