# LipiCore Bank Staff AI Appliance

LipiCore is a private, white-label AI appliance for bank staff. It runs in bank-controlled infrastructure, uses local model endpoints, indexes approved internal documents, and returns staff-ready answers with source evidence, governance metadata, and audit records.

The product is designed for customer care, branch operations, compliance, document review, and internal knowledge workflows. It is not an autonomous decision engine. Lending, compliance, regulatory, operational, and customer-impact decisions remain with authorized bank staff.

## What It Does

- **Chat over approved knowledge:** Staff ask questions against approved bank documents with page, section, chunk, and passage-level source evidence.
- **Policy citation fidelity:** Policy, procedure, circular, directive, SOP, law, act, and compliance answers cite document heading, clause number, PDF page, printed page when available, and source status; incomplete policy citations are blocked for review instead of presented as final answers.
- **Session uploads:** Users can upload files inside a chat session without leaking those files into other sessions.
- **Document Library:** Bank documents are uploaded, extracted, chunked, embedded, indexed, governed, approved, superseded, archived, or disabled.
- **Queued ingestion:** Redis/RQ workers process extraction, OCR, table parsing, chunking, embeddings, Qdrant indexing, and long-document jobs outside the API request path.
- **Hybrid retrieval:** PostgreSQL full-text retrieval and Qdrant vector retrieval are merged, reranked, access-filtered, and citation-verified.
- **Long-document analysis:** Large PDFs, OCR-heavy files, and detailed Excel reviews run as background jobs with stored results.
- **OCR extraction:** Staff can extract OCR/text from files without adding those files to the approved knowledge base.
- **Evaluation Center:** Analytics-capable roles can run RAG evaluation packs before demos, pilots, model changes, prompt changes, ingestion changes, or embedding changes.
- **Bank readiness analytics:** Operational readiness combines document governance, evaluation status, ingestion health, queue state, and deployment evidence.
- **Internal banking workspace:** Super Admin can turn employee search, Staff Inbox, CEO messages, notifications/alerts, forex/time/date utilities, knowledge-gap queues, policy-change tracking, audit packs, and banking workflow helpers on or off per bank.
- **Staff Messenger:** Internal bank-scoped messaging and attachments are available as a separate add-on and are not indexed into RAG.
- **White-label branding:** Product name, bank name, colors, welcome text, support contact, disclaimer, and allowed assistant modes are configurable per bank.

## Non-Claims

LipiCore does not claim to:

- approve or reject loans;
- replace compliance officers, supervisors, auditors, or authorized reviewers;
- guarantee regulatory correctness independent of the bank's approved and current documents;
- perfectly understand handwritten notes, signatures, seals, complex charts, or every scanned table;
- provide whole-bank HA/SLA guarantees without the corresponding HA architecture and retained test evidence;
- outperform public frontier models in general knowledge.

## Stack

- **Frontend:** React, Vite, Tailwind CSS, Material Symbols, Playwright tests.
- **Backend:** FastAPI, SQLModel, PostgreSQL, Alembic.
- **Retrieval:** Qdrant vectors plus PostgreSQL full-text search.
- **Embeddings:** `BAAI/bge-m3`, 1024 dimensions, normalized vectors by default.
- **Workers:** Redis/RQ for ingestion and long-document analysis.
- **Storage:** MinIO-compatible object storage for uploaded files.
- **Models:** OpenAI-compatible local vLLM endpoints routed as fast/deep routes (legacy labels `LipiFast` and `LipiCore`) with optional vision/OCR routes.
- **Deployment:** Docker Compose for pilots; HA reference architecture under `deploy/ha/`.

## Current Retrieval Defaults

- Default text chunk profile: 1000 characters with 200 overlap.
- Regulatory/profiled documents: 900 characters with 180 overlap.
- OCR-heavy pages: 800 characters with 100 overlap.
- Spreadsheets: 1600 characters with 120 overlap.
- Presentations: 900 characters with 120 overlap.
- Chat memory: recent conversation context is packed into the prompt; retrieval remains source-governed through approved/session document filters.

## Local Development

Backend:

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password pytest -q
```

Frontend:

```bash
cd frontend
npm install
npm run lint
npm run build
```

Compose stack:

```bash
cp .env.example .env
./deploy/upgrade.sh
```

Run migrations after schema changes:

```bash
docker compose exec backend alembic upgrade head
```

## Main URLs

- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- Qdrant: `http://localhost:6333`
- MinIO console: `http://localhost:9001`
- RAG evaluations: `/evaluations`
- Model Lab: `/model-lab`
- Employee Search: `/employees`
- Forex, Time & Dates: `/market-time`
- Notifications & Alerts: `/notifications`
- CEO's Message: `/ceo-messages`
- Super Admin feature controls: `/admin/features`

## Documentation

Start with [docs/README.md](docs/README.md).

- [Architecture](docs/architecture.md)
- [Deployment and operations](docs/deployment.md)
- [Security architecture](docs/security.md)
- [Internal banking workspace](docs/internal-banking-workspace.md)
- [Long-document analysis](docs/long-document-analysis.md)
- [RAG evaluation sets](docs/evaluations/README.md)
- [Bank readiness checklist](docs/deployment/bank-readiness-checklist.md)
- [Production sizing tiers](docs/sizing/production-tiers.md)
- [HA reference architecture](deploy/ha/README.md)

## Release Discipline

Before a bank demo, pilot, or production release:

1. Run migrations.
2. Run backend tests and frontend lint/build.
3. Upload representative PDF, scanned PDF, DOCX, XLSX, PPTX, TXT/CSV, and image files.
4. Run the bank-specific RAG evaluation gate.
5. Check model health, Redis queue depth, ingestion worker logs, GPU memory, and storage growth.
6. Confirm backup and restore evidence for PostgreSQL, MinIO, and Qdrant.

Single-host Docker Compose is suitable for pilots and controlled trials. Whole-bank deployments require HA PostgreSQL, Qdrant replication/snapshots, Redis HA or accepted queue-loss policy, object-storage durability, backend/frontend replicas, model capacity planning, monitoring, and restore drills.
