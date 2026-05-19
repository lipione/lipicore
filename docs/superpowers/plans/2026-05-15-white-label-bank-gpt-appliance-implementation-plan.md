# White-Label Bank GPT Appliance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade BankAi into a white-label, airgapped, GPT-style bank assistant that all staff can use, with strong RAG, citations, document governance, audit logs, and appliance operations.

**Architecture:** Keep the existing FastAPI, React, PostgreSQL, Qdrant, Redis, MinIO, nginx, and vLLM stack. Add a white-label configuration layer, a unified AI request gateway, a source-backed answer contract, document governance, production-safe frontend assets, and appliance operations tooling.

**Tech Stack:** FastAPI, SQLModel, Alembic, PostgreSQL, Qdrant, Redis, MinIO, React/Vite, Tailwind CSS, Docker Compose, nginx, vLLM, pytest, Playwright.

---

## Product Direction

Build one excellent ChatGPT-style staff assistant first. Do not build department-specific apps in V1. Departments can appear as document metadata, access filters, and prompt examples, but the user experience is one universal assistant.

## Milestone 0: Runtime And Repo Hygiene

**Goal:** Make the project installable and testable before feature work.

**Files:**
- Create: `backend/.python-version`
- Modify: `backend/Dockerfile`
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] Add `backend/.python-version`.

```text
3.11
```

- [ ] Ensure `backend/Dockerfile` uses Python 3.11.

```dockerfile
FROM python:3.11-slim
```

- [ ] Add `.superpowers/` to `.gitignore`.

```gitignore
.superpowers/
```

- [ ] Document setup commands in `README.md`.

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest -q

cd ../frontend
npm install
npm run build
npm run lint
```

- [ ] Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest -q
cd ../frontend
npm run build
npm run lint
```

Expected: backend tests collect under Python 3.11; frontend build passes; lint has no errors.

## Milestone 1: White-Label Foundation

**Goal:** Make product name, logo, colors, prompts, and support text configurable per bank.

**Files:**
- Create: `backend/app/models/branding.py`
- Create: `backend/app/schemas/branding.py`
- Create: `backend/app/api/branding.py`
- Create: `backend/alembic/versions/004_branding_settings.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/config/branding.js`
- Create: `frontend/src/hooks/useBranding.js`
- Modify: `frontend/src/pages/Login.jsx`
- Modify: `frontend/src/pages/ChatAssistant.jsx`
- Modify: `frontend/src/layouts/MainLayout.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] Create the branding model.

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class BrandingSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True, unique=True)
    product_name: str = "Bank GPT"
    bank_name: str = "Bank"
    short_bank_name: str = "Bank"
    primary_color: str = "#0b1c30"
    accent_color: str = "#0051d5"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    welcome_message_en: str = "Namaste. Ask approved bank knowledge or upload a document."
    welcome_message_ne: str = "नमस्ते। स्वीकृत बैंक ज्ञान सोध्नुहोस् वा कागजात अपलोड गर्नुहोस्।"
    support_contact: Optional[str] = None
    disclaimer_text: str = "AI suggestions are for internal staff assistance. Follow approved bank policy and escalation rules."
    allowed_modes_json: str = "[\"bank_knowledge\", \"uploaded_file\", \"summarize\", \"draft\", \"translate\", \"compare\"]"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] Add public endpoint `GET /api/branding/public`.
- [ ] Add admin endpoint `PATCH /api/branding`.
- [ ] Frontend loads branding before rendering protected layout.
- [ ] Replace hardcoded `LipiCore`, `BankAi`, and default welcome text in primary UI.
- [ ] Add tests for default branding and bank-specific branding.

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_branding.py -q
cd ../frontend
npm run build
```

## Milestone 2: GPT-Style Chat UX

**Goal:** Make chat the product, not a secondary feature.

**Files:**
- Modify: `frontend/src/pages/ChatAssistant.jsx`
- Create: `frontend/src/components/chat/ChatModeSelector.jsx`
- Create: `frontend/src/components/chat/AnswerTrustBadge.jsx`
- Create: `frontend/src/components/chat/SourceEvidencePanel.jsx`
- Create: `frontend/src/components/chat/SavedAnswerButton.jsx`
- Modify: `frontend/src/components/chat/FilePreviewCard.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] Make `/chat` the post-login default route.
- [ ] Add modes:
  - `Ask Bank Knowledge`
  - `Analyze Uploaded File`
  - `Summarize`
  - `Draft`
  - `Translate`
  - `Compare`
- [ ] Keep one text input and one upload control.
- [ ] Show answer trust state above every assistant answer.
- [ ] Move sources into a right-side source evidence panel on desktop and a drawer on mobile.
- [ ] Fix `MsgBubble` source rendering by passing active document/source state as props or removing out-of-scope references.
- [ ] Add example prompt chips from branding config.
- [ ] Add Playwright smoke test for starting a chat and rendering a source-backed answer with mocked API.

Verify:

```bash
cd frontend
npm run build
npm run lint
npm run test:e2e -- --grep "chat"
```

## Milestone 3: Unified AI Request Gateway

**Goal:** Every LLM path uses one security, retrieval, model, and audit pipeline.

**Files:**
- Create: `backend/app/services/ai_request_gateway.py`
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/api/tasks.py`
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_ai_request_gateway.py`

- [ ] Define request modes.

```python
from enum import Enum

class AiMode(str, Enum):
    BANK_KNOWLEDGE = "bank_knowledge"
    UPLOADED_FILE = "uploaded_file"
    SUMMARIZE = "summarize"
    DRAFT = "draft"
    TRANSLATE = "translate"
    COMPARE = "compare"
```

- [ ] Define response contract.

```python
class AnswerType(str, Enum):
    SOURCE_BACKED = "source_backed"
    UPLOADED_FILE = "uploaded_file"
    GENERAL = "general"
    NOT_FOUND = "not_found"
    ESCALATE = "escalate"
```

- [ ] Gateway order:
  1. authenticate user
  2. validate mode
  3. prompt-injection screen
  4. PII masking according to policy
  5. resolve document scope
  6. enforce document access
  7. retrieve sources if mode requires RAG
  8. build prompt
  9. call selected local model
  10. emit audit event
  11. return answer contract

- [ ] Refactor `/chat/sessions/{session_id}/messages`, `/stream`, `/stream-file`, and `/tasks/run` through gateway.
- [ ] Add tests proving `/stream-file` no longer bypasses prompt-injection and PII handling.

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_ai_request_gateway.py -q
```

## Milestone 4: Best-RAG V1

**Goal:** Make source-backed retrieval the product advantage.

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/app/services/qdrant_service.py`
- Create: `backend/app/services/source_attribution_service.py`
- Test: `backend/tests/test_rag_answer_contract.py`
- Test: `backend/tests/test_session_documents.py`

- [ ] Official bank knowledge mode searches only approved/global documents the user can access.
- [ ] Uploaded file mode searches only current session uploads and selected active documents.
- [ ] Compare mode supports two or more selected documents.
- [ ] Every source includes:
  - document ID
  - document title
  - document type
  - page number when available
  - section label when available
  - chunk index
  - snippet
  - relevance score
- [ ] If no source meets threshold for bank policy/compliance questions, return `not_found`.
- [ ] Add regression tests for cross-session leakage, low-score not-found, source fields, and staff access restrictions.

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_rag_answer_contract.py tests/test_session_documents.py -q
```

## Milestone 5: Document Governance Lite

**Goal:** Admin can control which documents influence official answers.

**Files:**
- Modify: `backend/app/models/document.py`
- Modify: `backend/app/schemas/document.py`
- Modify: `backend/app/api/documents.py`
- Create: `backend/app/services/document_policy_service.py`
- Create: `backend/alembic/versions/005_document_governance_lite.py`
- Modify: `frontend/src/pages/Documents.jsx`
- Test: `backend/tests/test_document_policy.py`

- [ ] Add fields:
  - `lifecycle_status`
  - `approved_by`
  - `approved_at`
  - `owner_department`
  - `effective_date`
  - `expiry_date`
- [ ] Valid lifecycle statuses:
  - `draft`
  - `indexed`
  - `approved`
  - `superseded`
  - `archived`
  - `disabled`
- [ ] RAG only uses `approved` documents for official bank knowledge.
- [ ] Session uploads remain available only inside their owning session.
- [ ] Add approve/disable actions in Documents UI for bank admins.

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_document_policy.py -q
```

## Milestone 6: Staff-Wide Admin Controls

**Goal:** Make staff onboarding into the product safe and simple.

**Files:**
- Modify: `backend/app/api/users.py`
- Modify: `backend/app/schemas/user.py`
- Modify: `frontend/src/pages/Users.jsx`
- Modify: `frontend/src/api/axios.js`
- Test: `backend/tests/test_users.py`

- [ ] Remove frontend hardcoded password.
- [ ] Remove frontend hardcoded `bank_id: 1`.
- [ ] Bank admin-created users inherit `current_user.bank_id`.
- [ ] Add temporary password or reset-token flow.
- [ ] Frontend redirects on both unauthenticated 401 and expired/invalid 403.
- [ ] Add role list suitable for all-staff MVP:
  - `super_admin`
  - `bank_admin`
  - `knowledge_admin`
  - `auditor`
  - `staff_user`

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_users.py -q
cd ../frontend
npm run build
```

## Milestone 7: Local Assets And Airgapped UI

**Goal:** The UI works without external internet.

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`
- Add: `frontend/src/assets/fonts/`
- Add: `frontend/src/components/icons/`

- [ ] Remove Google Fonts links.
- [ ] Remove Material Symbols remote stylesheet.
- [ ] Bundle fonts locally or use system font stack.
- [ ] Replace Material Symbols with local icon components or `lucide-react`.
- [ ] Verify no external requests are needed for initial render.

Verify:

```bash
cd frontend
npm run build
rg -n "fonts.googleapis|fonts.gstatic|Material Symbols|https://" dist src index.html
```

Expected: no required external font/icon dependency.

## Milestone 8: Appliance Operations MVP

**Goal:** Bank IT can see health and export diagnostics.

**Files:**
- Create: `backend/app/services/health_service.py`
- Create: `backend/app/api/operations.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/pages/ApplianceHealth.jsx`
- Modify: `frontend/src/App.jsx`
- Test: `backend/tests/test_operations.py`

- [ ] Health API checks:
  - backend
  - Postgres
  - Qdrant
  - Redis
  - MinIO
  - vLLM fast
  - vLLM deep
  - disk free
  - model status
- [ ] Endpoint requires `bank_admin` or `super_admin`.
- [ ] Diagnostic export redacts secrets.
- [ ] Frontend shows health cards and operator hints.

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_operations.py -q
cd ../frontend
npm run build
```

## Milestone 9: Production Deployment Hardening

**Goal:** Test server can move toward client-appliance shape.

**Files:**
- Modify: `docker-compose.yml`
- Modify: `nginx.conf`
- Modify: `.env.example`
- Create: `deploy/offline/preflight.sh`
- Create: `deploy/offline/backup.sh`
- Create: `deploy/offline/restore.sh`
- Create: `docs/appliance/offline-install-guide.md`
- Create: `docs/appliance/backup-restore-runbook.md`

- [ ] Do not publish backend, frontend, Qdrant, Redis, MinIO, Postgres, or vLLM ports publicly by default.
- [ ] Bind debug ports to `127.0.0.1` when needed.
- [ ] Disable public OpenAPI docs in production via config.
- [ ] Add backup script for Postgres, Qdrant, MinIO, and `.env`.
- [ ] Add restore script and documented restore test.
- [ ] Add offline preflight checks for Docker, NVIDIA runtime, disk, RAM, model paths, ports, and env.

Verify on staging/test server:

```bash
docker compose config
docker compose up -d --build
curl -I https://ai.silverlining.com.np
curl -sS https://ai.silverlining.com.np/health
```

Expected: public access only through nginx; internal service ports unavailable externally.

## Milestone 10: Evaluation And Pilot Readiness

**Goal:** Prove quality before client rollout.

**Files:**
- Create: `backend/app/models/evaluation.py`
- Create: `backend/app/services/evaluation_service.py`
- Create: `backend/app/api/evaluations.py`
- Create: `docs/appliance/pilot-playbook.md`
- Create: `docs/appliance/buyer-packet.md`

- [ ] Create 50-question initial evaluation set.
- [ ] Track citation correctness, not-found correctness, latency, and source presence.
- [ ] Keep human answer correctness as manually scored field.
- [ ] Create pilot playbook for one bank:
  - users: 20-50 staff
  - corpus: 500-2,000 documents
  - duration: 90 days
  - metrics: usage, source accuracy, response latency, staff satisfaction, admin effort
- [ ] Create buyer packet:
  - product one-liner
  - architecture
  - deployment model
  - security controls
  - limitations
  - support process

Verify:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_evaluation_service.py -q
```

## V1 Release Gate

Do not call this client-ready until:

- backend tests run under Python 3.11
- frontend build passes
- chat UX is the primary product
- white-label config works without code edits
- all LLM request paths use the unified gateway
- official bank answers cite sources or refuse
- document approval controls official knowledge
- user creation has no hardcoded password or bank ID
- external fonts/icons are removed
- appliance health page works
- backup and restore scripts exist
- public OpenAPI docs can be disabled
- debug/internal ports are not exposed in production compose

## V2 Direction

After V1 usage data, add department workflow templates:
- Customer Care staff assistant
- Staff onboarding
- Credit memo assistant
- Operations SOP navigator
- Compliance circular review

Do not build these before the universal assistant is excellent.
