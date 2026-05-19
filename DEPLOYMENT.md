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
| `LLM_A_API_BASE` | Fast vLLM OpenAI-compatible endpoint base URL | `http://vllm-b:8000` |
| `LLM_C_API_BASE` | Deep vLLM OpenAI-compatible endpoint base URL | `http://vllm-c:8000` |
| `REDIS_URL` | Model admission-control Redis URL | `redis://redis:6379/0` |

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
*   `lipicore-vllm-b` / `lipicore-vllm-c`: Ensure local vLLM model servers are running and reachable from the backend.

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
5.  **HA Reality:** Single-host Docker Compose is not a high-availability architecture. Use `deploy/ha/README.md` for whole-bank planning.
