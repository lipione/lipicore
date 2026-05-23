# BankAi: Deployment Guide

This guide covers the steps required to deploy BankAi in a production or staging environment.

## 1. Prerequisites
*   **Operating System:** Ubuntu 22.04 LTS (recommended) or any system with Docker support.
*   **Hardware:**
    *   Minimum 16GB RAM for app-only testing; 64GB+ recommended when running local models.
    *   NVIDIA GPU sized for the selected vLLM model tier.
*   **Software:** Docker 24.0+, Docker Compose 2.20+.

## 2. Environment Configuration

Copy the example environment file and configure the secrets:
```bash
cp .env.example .env
```

### Essential Variables:
| Variable | Description | Recommended |
| :--- | :--- | :--- |
| `JWT_SECRET` | Secret key for auth tokens | Generate a random 64-char string |
| `POSTGRES_PASSWORD` | Database password | Secure random string |
| `LLM_A_API_BASE` | Primary text vLLM OpenAI-compatible endpoint base URL | `http://vllm-c:8000` on current production |
| `LLM_B_API_BASE` | Secondary text vLLM endpoint when enabled | Same as `LLM_A_API_BASE` on current production |
| `LLM_C_API_BASE` | Analyst/deep vLLM OpenAI-compatible endpoint base URL | `http://vllm-c:8000` |
| `LLM_VISION_API_BASE` | Vision/OCR vLLM endpoint when enabled | `http://vllm-vision:8000` or production override |
| `REDIS_URL` | Model admission-control Redis URL | `redis://redis:6379/0` |
| `INGESTION_JOB_TIMEOUT_SECONDS` | Timeout for ingestion and queued long-document jobs | `1800` |
| `INGESTION_WORKER_CONCURRENCY` | Worker concurrency for ingestion and long-document analysis | `1` for pilots |
| `OCR_MAX_PAGES` | Max pages for scanned-PDF OCR fallback | `200` |
| `LLM_DEEP_CONTEXT_WINDOW_TOKENS` | Context budget for queued long-document analysis | Match deployed deep model |

---

## 3. Deployment Steps

### Step 1: Clone and Build
```bash
git clone <repo-url>
cd BankAi
cp .env.example .env
# edit .env with production secrets and model paths
./deploy/upgrade.sh
```

### Step 2: Database Migration
For normal releases, use Alembic:
```bash
docker compose exec backend alembic upgrade head
```

`./deploy/upgrade.sh` already runs migrations as part of the standard upgrade path.

### Step 3: Verify Services
Check the health of the containers:
```bash
docker compose ps
./deploy/upgrade.sh --check-only
```
*   `backend`: Should report healthy.
*   `frontend`: Should report healthy.
*   `nginx`: Should report healthy.
*   `redis`: Should report healthy.
*   `bankai-qdrant`: Should be listening on 6333.
*   `lipicore-vllm-c`: Ensure the current text/analyst vLLM model server is running and reachable from the backend.
*   `lipicore-vllm-vision`: Ensure the vision/OCR vLLM server is running if image or OCR analysis is enabled.

Current production note: `/data/bankai` routes `LLM_A`, `LLM_B`, and `LLM_C`
to `lipicore-vllm-c` / Gemma 4 26B 4-bit, and routes vision/OCR work to
`lipicore-vllm-vision` / Qwen3-VL 8B. `lipicore-vllm-b` is not active on that
server profile.

---

## 4. Production Hardening

### SSL/TLS Termination
It is strongly recommended to place BankAi behind a reverse proxy like **Nginx** or **Traefik** to handle SSL certificates.

Example Nginx config:
```nginx
server {
    listen 443 ssl;
    server_name bankai.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

### Security Considerations
1.  **VPC Isolation:** Ensure the database and vector engine are not accessible from the public internet.
2.  **Firewall:** Only allow traffic on port 443 (HTTPS) and port 22 (SSH).
3.  **MinIO:** Configure MinIO with a private bucket and rotate access keys regularly.
4.  **RAG Evaluation:** Run `/evaluations` before customer demos and after changes to ingestion, prompts, embeddings, retrieval, or models.
5.  **Long-Document Analysis:** Queue heavy OCR/PDF/XLS jobs through Document Library and monitor Redis/worker/deep-model load. Do not promise instant large-file turnaround without evidence.
6.  **HA Reality:** Single-host Docker Compose is not a high-availability architecture. Use `deploy/ha/README.md` for whole-bank planning.
