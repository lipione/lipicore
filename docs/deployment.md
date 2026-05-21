# Deployment Guide

## Docker Compose Deployment

The current deployment runs as a private Docker Compose stack with FastAPI, React/Vite, PostgreSQL, Qdrant, Redis, MinIO, nginx, and local vLLM model servers.

1. Provision Ubuntu 22.04 LTS or a compatible Linux host.
2. Install Docker, Docker Compose, and the NVIDIA container runtime if GPU inference is enabled.
3. Clone the repository and configure `.env` with strong secrets and local model endpoints.
4. Place approved local model weights under the host model volume expected by `docker-compose.yml`.
5. Run:
   ```bash
   ./deploy/upgrade.sh
   ```

## Runtime Services

- `backend`: FastAPI orchestration, auth, RAG, evaluation, audit, upload queuing, and streaming.
- `ingestion-worker`: Redis/RQ worker that extracts, chunks, embeds, indexes, summarizes, catalogs uploaded documents, and runs queued long-document analysis jobs.
- `frontend`: React/Vite UI served by nginx.
- `db`: PostgreSQL metadata and full-text retrieval indexes.
- `qdrant`: Vector search.
- `redis`: Model admission control and document ingestion queue.
- `minio`: Object storage for uploaded documents.
- `vllm-b` / `vllm-c`: Local OpenAI-compatible model servers for fast and deeper responses.
- `vllm-vision`: Optional profile-gated OpenAI-compatible vision/OCR endpoint for Qwen3-VL. Start with `docker compose --profile vision up -d vllm-vision` only after reserving enough GPU memory.

## Production Considerations

- Keep database, Qdrant, Redis, MinIO, and vLLM ports private.
- Terminate TLS at nginx or an approved enterprise reverse proxy.
- Run `POST /api/evaluations/rag` against bank-specific eval sets before claiming RAG quality.
- Back up PostgreSQL, MinIO, and Qdrant together so document metadata and vector payloads stay consistent.
- Keep `INGESTION_WORKER_CONCURRENCY=1` for pilot servers unless ingestion tests prove spare CPU/RAM/GPU capacity. Increase worker concurrency before increasing upload limits.
- Treat queued long-document analysis as worker and deep-model load. Monitor Redis queue depth, failed RQ jobs, deep-model queue time, and GPU memory before allowing large batches of OCR/PDF/XLS work.
- Use Compose health status during upgrades. `backend`, `frontend`, `redis`, and `nginx` should report healthy before handing the system back to bank staff.
- Use `./deploy/upgrade.sh --check-only` for health-only checks and `./deploy/upgrade.sh --run-tests` on the test server before shipping changes. The script defaults to the internal backend health URL because some data centers do not allow the server to curl its own public domain.
- For whole-bank HA planning, use `deploy/ha/README.md` and treat single-host Docker Compose as non-HA regardless of restart policies.

## Long-Document Analysis Operations

Long-document jobs use the same Redis/RQ worker path as ingestion. Run migrations before enabling the UI so `long_document_analysis_job` exists:

```bash
docker compose exec backend alembic upgrade head
```

Useful checks:

```bash
docker compose logs --tail=100 ingestion-worker
docker compose logs --tail=100 redis
docker compose logs --tail=100 backend
```

See `docs/long-document-analysis.md` for API details, role rules, and current limits.
