# BankAi: White-Label Bank GPT Appliance

BankAi is an airgapped, white-label internal AI assistant for banks. It is deployed with the bank's own infrastructure, runs private models locally, and gives staff a familiar GPT-style workspace for approved bank knowledge, document analysis, summarization, drafting, translation, and comparison.

This is not a generic SaaS chatbot. The product direction is a dedicated bank appliance: one deployment per institution, bank-controlled data, bank-branded UI, local model runtime, auditable usage, and source-backed answers from approved documents.

## Product Boundary

BankAi/LipiCore is a secure staff-assistance and decision-support system. It is not an autonomous decision engine. Final lending, compliance, regulatory, operational, and customer-impact decisions remain with authorized bank staff.

The first product use case is a **Bank Staff AI Helpdesk** for customer-care, branch, operations, compliance/helpdesk, and product/policy teams. It helps staff search approved knowledge, analyze internal files, summarize, draft, compare, and translate inside bank-controlled infrastructure.

## Key Features

### Enterprise Chat Experience
*   **White-label branding:** Product name, bank name, colors, welcome text, support contact, disclaimer, and allowed assistant modes are configurable per bank.
*   **Asynchronous Document Ingestion:** Upload PDF, DOCX, XLSX, PPTX, CSV, TXT, and image-heavy files without blocking chat. Processing runs through a Redis/RQ worker.
*   **Queued Long-Document Analysis:** Large PDFs, OCR-heavy documents, and detailed Excel/PDF reviews can be queued as background jobs, packed into relevant excerpts, and reviewed later from the Document Library.
*   **Real-time Progress Tracking:** Document Library cards show queued, extracting, embedding, indexing, and ready states.
*   **Conversational Memory:** 10-message sliding window memory ensuring contextual follow-up awareness.
*   **Stop & Regenerate:** Full control over generation with the ability to stop long-running streams or regenerate previous responses.

### Advanced RAG & Governance
*   **Session-Bound Isolation:** Secure context routing ensuring that documents uploaded in one chat session are never leaked to another.
*   **Source Evidence:** Assistant answers show source documents, snippets, full passages, page/section/chunk metadata, relevance, and citation-verification status.
*   **RAG Evaluation Center:** Admin and audit roles can run JSON evaluation sets to test source recall, citation term recall, answer term recall, and not-found behavior.
*   **Document Governance:** Knowledge documents support draft, approved, superseded, archived, and disabled lifecycle states.
*   **Predictive Follow-ups:** Dynamically generated follow-up questions at the end of every response to guide user investigation.
*   **Audit Logging:** Comprehensive logging of queries, file uploads, and AI responses for bank review and governance.
*   **Large File Governance:** Long-document jobs keep staff analysis separate from normal chat, store result metadata, and keep final interpretation with bank staff.

### Security & Privacy
*   **Data Sovereignty:** Fully air-gapped capable; runs with local vLLM model servers and self-hosted vector databases (Qdrant).
*   **PII Masking:** Automatic detection and masking of sensitive Personally Identifiable Information (PII) before LLM processing.
*   **RBAC:** Role-Based Access Control for staff, admin, audit, data audit, bank admin, and super admin users with bank-level partitioning.

### Explicit Non-Claims
BankAi/LipiCore does not currently claim to:

*   Make lending decisions or approve/reject credit.
*   Replace compliance officers, supervisors, or authorized bank reviewers.
*   Guarantee regulatory correctness independent of the bank's approved and current documents.
*   Fully understand every scanned PDF, complex table, seal, signature, or handwritten note.
*   Provide a blanket production HA/SLA guarantee without the corresponding HA deployment architecture.
*   Be generally better than GPT-4, GPT-5, Claude, Gemini, or other public frontier models.

---

## Tech Stack

*   **Frontend:** React (Vite), Tailwind CSS, Material Symbols.
*   **Backend:** FastAPI (Python 3.12), SQLModel, PostgreSQL 15.
*   **Vector Engine:** Qdrant (Semantic Search & Session Filtering).
*   **LLM Orchestration:** vLLM with Redis-backed admission control for private local inference.
*   **Ingestion Queue:** Redis/RQ worker for extraction, OCR/table parsing, embeddings, and indexing.
*   **Long-Document Queue:** Reuses Redis/RQ for large-file extraction, context packing, analyst-model generation, and persisted results.
*   **Storage:** MinIO (S3-compatible persistent storage).
*   **Streaming:** Server-Sent Events (SSE) for both generation and document status tracking.
*   **OCR Extraction Workspace:** Upload supported files and extract text through open-source Tesseract OCR and direct parsers without adding them to the approved knowledge base.
*   **Governance Workspaces:** Compliance Workspace, Model Lab, Evaluation Center, audit logs, and admin controls.

---

## Architecture

BankAi uses a decoupled **Worker-Observer** architecture for document processing:
1.  **Ingestion:** Files are uploaded to an async worker that handles OCR, chunking, and embedding.
2.  **Streaming:** The UI subscribes to an SSE status stream to update progress cards in real-time.
3.  **Retrieval:** Context is retrieved from Qdrant using `BAAI/bge-m3` multilingual embeddings and a session-aware metadata filter.
4.  **Reranking & Verification:** Retrieved candidates are reranked, filtered by relevance, and later checked by the citation verifier.
5.  **Admission Control:** Redis coordinates per-model and per-user concurrency so GPU memory is protected under load.
6.  **Generation:** Response is streamed token-by-token from the local vLLM runtime.

For heavy files, users should use the queued long-document workflow instead of normal chat. The workflow creates a background job, extracts PDF/OCR/Excel content, packs relevant excerpts into the analyst-model context, and stores the result for staff review. See [Queued Long-Document Analysis](docs/long-document-analysis.md).

---

## Deployment

### Prerequisites
*   Docker and Docker Compose.
*   NVIDIA container runtime for GPU-backed vLLM services.
*   Local LipiFast/LipiCore model files mounted on the inference host.
*   Python 3.12 for local backend development and tests.
*   Node.js 20+ for local frontend development.

### Quick Start

1.  **Clone the Repository:**
    ```bash
    git clone <repo-url>
    cd BankAi
    ```

2.  **Environment Setup:**
    ```bash
    cp .env.example .env
    # Configure secrets, public origin, model paths, and TLS settings for your host.
    ```

3.  **Run with the health-gated upgrade script:**
    ```bash
    ./deploy/upgrade.sh
    ```

4.  **Database Migration:**
    If you are updating from a previous version, run Alembic migrations:
    ```bash
    docker exec bankai-backend alembic upgrade head
    ```

For a health-only server check:

```bash
./deploy/upgrade.sh --check-only
```

### Local Development Checks

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

### White-Label Branding API

The frontend reads public branding from:
```http
GET /api/config/branding
GET /api/config/branding?bank_code=<BANK_CODE>
```

Bank admins and super admins can update branding:
```http
PATCH /api/config/branding/{bank_id}
```

Supported fields include `product_name`, `bank_name`, `logo_url`, `primary_color`, `accent_color`, `welcome_message`, `support_contact`, `disclaimer`, and `allowed_modes`.

### Access Points
*   **Frontend UI:** `http://localhost:3000`
*   **API Documentation:** `http://localhost:8000/docs`
*   **MinIO Console:** `http://localhost:9001`
*   **RAG Evaluation Center:** `/evaluations`

### Current Production Access

*   **Public UI:** `https://ai.silverlining.com.np`
*   **Text model route:** all current text routes are presented as LipiCore on the production server.
*   **Open-source OCR:** Tesseract handles image and scanned-PDF text extraction; LipiCore handles optional document-image review notes where enabled.
*   **LipiFast route:** not active in the current production server profile; do not start a separate fast endpoint without a GPU capacity decision.
*   **Queueing:** Redis limits concurrent requests per model and per user.
*   **Deployed commit:** `615d299` in `/data/bankai`.

---

## ⚖️ Disclaimer
This system is designed for private banking infrastructure. Production deployments should enforce TLS/SSL, strict network isolation, formal backup/restore procedures, and enterprise IAM integration where required. Single-host Docker Compose is suitable for pilots and controlled trials, not a standalone high-availability guarantee.
