# Airgapped BankAi Product Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade BankAi from a broad banking RAG demo into a credible airgapped compliance and policy intelligence appliance that banks can pilot, evaluate, procure, and operate inside their own infrastructure.

**Architecture:** Keep the current FastAPI, React, PostgreSQL, Qdrant, Redis, MinIO, nginx, and vLLM stack, but turn it into an appliance-grade product with strict security gates, measurable RAG evaluation, offline install/upgrade tooling, operator observability, and a narrow compliance workflow. The product must prove document isolation, source-backed answers, auditability, and operational reliability before making enterprise claims.

**Tech Stack:** FastAPI, SQLModel, PostgreSQL, Qdrant, Redis, MinIO, React/Vite, Tailwind, Docker Compose, nginx, vLLM, local embedding models, pytest, Playwright, offline deployment bundle scripts.

---

## How To Use This Plan

This document has two audiences:

1. **Founder, investor, and client reviewers** should read the Research Basis, Brutal Product Thesis, Executive Upgrade Roadmap, Product Scope, Commercial Upgrade Plan, Risks, and Release Gates. Those sections define whether this can become a credible product.
2. **Engineering teams** should execute the Milestone Roadmap task by task. Those sections are intentionally concrete because vague strategy will not survive a bank security review.

The plan is not a marketing roadmap. It is a credibility repair plan. The product should not be shown to serious bank buyers as "client-ready" until the Pilot Gate is passed.

## Research Basis

The market is real, but crowded. Sovereign and airgapped AI is now an explicit enterprise category, not a novelty. HPE has added airgapped features and secure deployment options to Private Cloud AI in response to enterprise sovereignty, security, and compliance demand. Appliance-style AI vendors increasingly position around regulated industries, data sovereignty, auditability, and governed local inference.

The bank buyer will not accept "chat with documents" as differentiation. The product must be positioned as an airgapped compliance and policy intelligence system for banks that cannot send internal documents, circulars, SOPs, and policies to cloud AI.

Regulatory expectations matter. OCC 2026 model risk guidance highlights governance, controls, vendor-product considerations, validation, and monitoring even while noting that generative and agentic AI are rapidly evolving and outside that specific guidance scope. Federal Reserve model risk guidance stresses model development, validation, governance, policies, controls, documentation, and senior-management oversight. NIST AI RMF and NIST AI 600-1 provide a practical AI-risk framework for generative AI. ISO/IEC 42001 frames AI management systems around responsible use, risk management, traceability, transparency, and governance. OWASP LLM Top 10 identifies LLM-specific security risks, including prompt injection and RAG-related attack paths. EnterpriseRAG-Bench shows that realistic enterprise RAG evaluation needs noisy, conflicting, multi-source internal knowledge and unanswerable questions.

### Research References

- [HPE Private Cloud AI air-gapped release notes](https://support.hpe.com/hpesc/public/docDisplay?docId=sd00007093en_us&docLocale=en_US&page=GUID-694A8AA6-795D-41EC-948A-54EE2FF6A6F0.html)
- [HPE AI factory and Private Cloud AI announcement](https://www.hpe.com/us/en/newsroom/press-release/2025/06/hpe-unveils-new-ai-factory-solutions-built-with-nvidia-to-accelerate-ai-adoption-at-global-scale.html)
- [OCC Bulletin 2026-13: Model Risk Management](https://occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html)
- [Federal Reserve SR 11-7: Model Risk Management](https://www.federalreserve.gov/bankinforeg/srletters/sr1107.htm)
- [NIST AI 600-1: Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
- [ISO/IEC 42001 overview](https://www.iso.org/es/contents/data/standard/08/12/81230.html)
- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [EnterpriseRAG-Bench paper](https://arxiv.org/abs/2605.05253)

## Brutal Product Thesis

BankAi should stop selling itself as a generic "private banking AI assistant." That is weak positioning and invites direct comparison with Microsoft Copilot, Glean, Hebbia, AlphaSense, and dozens of private-AI platforms.

The viable wedge is:

**Airgapped policy and compliance intelligence for banks, delivered with private infrastructure, local models, source-backed answers, audit trails, and controlled document governance.**

The first client-ready product should serve compliance, risk, internal audit, and policy operations. General staff chat can come later.

## Executive Upgrade Roadmap

### Horizon 1: Credibility Repair

**Timeframe:** 2-4 weeks
**Business purpose:** Stop the product from failing basic technical and security review.
**Outcome:** The team can honestly say the prototype has working tests, consistent security controls, controlled uploads, no hardcoded user credentials, and no unsupported compliance/SLA claims.

Deliverables:
- Python 3.11 backend runtime and passing test collection.
- Unified upload limits across document, chat, and task endpoints.
- Every request-time LLM path routed through the same security, masking, access, and audit layer.
- No frontend hardcoded password or bank ID.
- Runtime crash in source rendering fixed.
- Product documentation stripped of unsupported claims.

### Horizon 2: Compliance MVP

**Timeframe:** 4-8 weeks
**Business purpose:** Stop selling a generic chat surface and create one bank-buyer workflow.
**Outcome:** A compliance officer can use approved internal documents to ask policy questions, inspect cited evidence, and export a source-backed memo.

Deliverables:
- Governed Policy and Circular Library.
- Document lifecycle: draft, indexed, reviewed, approved, superseded, archived, disabled.
- Compliance Workspace as primary UI.
- Evidence-first answer contract with source-backed and not-found answer types.
- Memo export with citations and document versions.
- Audit trail for question, answer, user, model profile, retrieval query, and sources.

### Horizon 3: Airgapped Appliance Readiness

**Timeframe:** 8-12 weeks
**Business purpose:** Make deployment repeatable enough that the business is not just custom services.
**Outcome:** Bank IT can install, operate, diagnose, back up, and upgrade the system without internet access and without founder heroics.

Deliverables:
- Offline preflight, install, upgrade, rollback, and checksum tooling.
- Operations Console for service health, model queues, ingestion failures, disk/GPU state, backup freshness, and diagnostics.
- Appliance documentation: admin manual, security architecture, backup/restore runbook, model governance, offline install guide.
- Evaluation Center with pilot threshold reporting.
- Buyer packet and pilot playbook.

## Client And Investor Proof Gates

### What A Bank Client Must Believe

- Its documents never leave bank-controlled infrastructure.
- Only approved and authorized documents influence answers.
- Answers cite exact evidence or refuse.
- Staff can be restricted by role, document scope, and department.
- Audit can reconstruct who asked what, what sources were used, and what model profile generated the answer.
- Bank IT can operate the appliance without vendor access to sensitive data.
- Backup, restore, upgrades, and rollback are not improvised.

### What An Investor Must Believe

- This is not a commodity RAG wrapper.
- The initial wedge is narrow enough to sell: airgapped compliance and policy intelligence for banks.
- The product can be deployed repeatedly, not rebuilt per client.
- The company can turn pilots into annual appliance, software, and support revenue.
- The moat can develop through regulated-bank deployment expertise, local corpus/evaluation assets, workflow depth, and procurement trust.

### Evidence Required Before Strong Claims

| Claim | Evidence Required |
|---|---|
| Secure | security tests, access-control tests, documented threat model, no known critical bypasses |
| Airgapped | clean offline install on a target-like machine, no required outbound network calls |
| Accurate | evaluation set results with answer, citation, refusal, and latency metrics |
| Bank-ready | pilot packet, security architecture, backup/restore proof, admin runbook |
| Reliable | health checks, recovery drills, upgrade/rollback test, monitoring evidence |
| Compliant | actual certification or explicit mapping to controls; no implied certification |

## Non-Negotiable Upgrade Principles

1. Do not claim SOC 2, ISO 27001, PCI DSS, HIPAA, NRB compliance, 99.95% uptime, ROI, or breach history unless evidence exists.
2. Every LLM path must pass through the same security, masking, logging, and access-control layer.
3. Every answer in compliance mode must be source-backed or explicitly say the answer was not found.
4. Every document must have lifecycle state: uploaded, indexed, reviewed, approved, superseded, archived, disabled.
5. Every deployment must work without internet access after installation.
6. Every release must include an offline upgrade package and rollback path.
7. Every client pilot must include accuracy, citation, latency, isolation, and usability measurements.

## Target Product Definition

### Product Name

**BankAi Compliance Knowledge Appliance**

### Primary Buyer

- Head of Compliance
- Head of Risk
- CIO / Head of IT
- Internal Audit leadership
- COO / Operations leadership in smaller institutions

### Primary Users

- Compliance officers
- Policy owners
- Risk analysts
- Internal auditors
- Branch operations supervisors
- Selected staff users after compliance validation

### Core Jobs

- Find the current approved answer to a policy or compliance question.
- Compare an internal policy against a regulatory circular.
- Generate a source-backed compliance memo.
- Prove which source documents informed an answer.
- Prevent unapproved, superseded, or unauthorized documents from influencing answers.
- Keep all data and inference inside the bank's infrastructure.

## Product Scope

### Keep

- Session chat with uploaded documents
- Approved global knowledge library
- Local vLLM inference
- Qdrant-backed retrieval
- Audit logging
- User roles
- Export
- English/Nepali support

### Reframe

- Chat becomes "Policy Q&A" and "Document Analysis."
- Documents become a governed "Policy and Circular Library."
- Audit logs become "AI Evidence and Activity Trail."
- Analytics become "Accuracy, Usage, and Operational Health."

### Deprioritize

- Generic dashboard vanity metrics
- Broad AI task templates
- Feature pages that do not support compliance/policy workflows
- Marketing-style claims without evidence

## Required Product Modules

### Module 1: Compliance Knowledge Library

Purpose: Govern documents before they are allowed to influence answers.

Capabilities:
- Upload documents into draft state.
- Extract text, chunk, embed, and index.
- Assign document type: policy, SOP, circular, directive, manual, report, other.
- Assign department and access level.
- Capture document version, effective date, expiry date, owner, and approval status.
- Mark documents as approved, superseded, archived, disabled.
- Prevent draft/superseded/disabled documents from RAG unless explicitly selected by an authorized reviewer.

### Module 2: Source-Backed Policy Q&A

Purpose: Give staff and compliance users controlled answers with citations.

Capabilities:
- Ask a question against approved documents.
- Optionally restrict to selected documents.
- Return answer with document title, page, section, chunk, and snippet.
- Return "not found" when sources do not support the answer.
- Show source evidence in a side panel.
- Support English and Nepali responses.
- Save question, answer, sources, model profile, retrieval query, and user identity to audit log.

### Module 3: Compliance Memo Generator

Purpose: Convert source-backed answers into work product.

Capabilities:
- Generate memo from selected answer and sources.
- Include scope, answer, cited evidence, limitations, reviewer, timestamp.
- Export PDF and DOCX.
- Preserve references to source documents and document versions.

### Module 4: AI Governance and Evaluation

Purpose: Prove the system is reliable enough to use.

Capabilities:
- Maintain a test set of policy/compliance questions.
- Track answer correctness, citation correctness, refusal correctness, latency, and isolation.
- Run evals against a release candidate before deployment.
- Store evaluation runs and compare model/retrieval changes.
- Provide an admin report for client security/procurement review.

### Module 5: Appliance Operations Console

Purpose: Make the installed system supportable by bank IT and the vendor.

Capabilities:
- Show service status for backend, frontend, Postgres, Qdrant, Redis, MinIO, vLLM, disk, GPU, RAM.
- Show model queue state and current concurrency limits.
- Show ingestion backlog and failed documents.
- Show backup status and last successful restore test.
- Export an offline diagnostic bundle.
- Provide operator runbooks for common failures.

### Module 6: Offline Installer and Upgrade System

Purpose: Make airgapped delivery repeatable.

Capabilities:
- Preflight script checks OS, disk, RAM, GPU, NVIDIA runtime, Docker, ports, mount paths.
- Install bundle contains app images, model manifests, embedding model, compose files, migrations, docs, checksum manifest.
- Upgrade script loads images, runs migrations, validates services, and supports rollback.
- License file works without internet access.
- Release notes clearly list schema changes, model changes, and rollback instructions.

## Architecture Upgrade

### Current Architecture To Keep

```text
React/Vite frontend
FastAPI backend
PostgreSQL metadata
Qdrant vector index
MinIO or local object/file storage
Redis model admission control
nginx TLS/proxy
vLLM local inference
Docker Compose deployment
```

### Required Architecture Changes

```text
Unified LLM Request Gateway
  - input validation
  - prompt-injection screening
  - PII masking policy
  - authorization context
  - retrieval policy
  - model routing
  - audit event emission

Document Governance Layer
  - document lifecycle
  - version state
  - approval policy
  - access policy
  - supersession handling

Evaluation Harness
  - fixtures
  - expected sources
  - expected refusals
  - run records
  - release gates

Appliance Operations Layer
  - health endpoints
  - diagnostics export
  - backup status
  - offline install/upgrade tooling
```

## File Structure Map

### Backend Files To Create

- `backend/app/core/runtime.py` - Python/runtime compatibility checks and settings.
- `backend/app/core/upload_limits.py` - shared upload limit and extension policy.
- `backend/app/services/llm_request_gateway.py` - single request path for all LLM calls.
- `backend/app/services/document_policy_service.py` - document visibility and lifecycle rules.
- `backend/app/services/evaluation_service.py` - evaluation run logic.
- `backend/app/services/health_service.py` - service checks for DB, Qdrant, Redis, MinIO, vLLM, disk, GPU.
- `backend/app/api/evaluations.py` - admin evaluation endpoints.
- `backend/app/api/operations.py` - appliance health and diagnostics endpoints.
- `backend/app/models/evaluation.py` - evaluation dataset and run records.
- `backend/app/schemas/evaluation.py` - evaluation request/response schemas.
- `backend/tests/test_security_llm_paths.py` - shared security tests for every LLM endpoint.
- `backend/tests/test_document_policy.py` - document lifecycle and access tests.
- `backend/tests/test_upload_limits.py` - upload size and extension tests.
- `backend/tests/test_evaluation_service.py` - evaluation scoring tests.
- `backend/tests/test_operations.py` - health endpoint tests.

### Backend Files To Modify

- `backend/requirements.txt` - pin runtime-compatible versions where required.
- `backend/app/api/chat.py` - route all chat and file streaming through `llm_request_gateway`.
- `backend/app/api/documents.py` - apply shared upload limits and lifecycle metadata.
- `backend/app/api/users.py` - replace hardcoded invitation behavior with server-side invite/reset flow.
- `backend/app/api/tasks.py` - route task LLM calls through `llm_request_gateway`.
- `backend/app/api/export.py` - include source metadata in memo exports.
- `backend/app/api/analytics.py` - replace vanity values with actual usage/eval/health metrics.
- `backend/app/services/rag_service.py` - enforce document policy and citation/refusal behavior.
- `backend/app/services/llm_service.py` - remove direct bypass paths or mark internal-only.
- `backend/app/services/llm_gateway.py` - correctly support fast, deep, and task model profiles.
- `backend/app/models/document.py` - add lifecycle fields.
- `backend/app/models/audit.py` - ensure LLM and document events are complete enough for review.
- `backend/app/main.py` - register evaluations and operations routers.
- `backend/alembic/versions/` - add schema migration for lifecycle and evaluation tables.

### Frontend Files To Create

- `frontend/src/pages/ComplianceWorkspace.jsx` - focused policy/compliance workflow.
- `frontend/src/pages/OperationsConsole.jsx` - appliance health and diagnostics UI.
- `frontend/src/pages/EvaluationCenter.jsx` - evaluation run dashboard.
- `frontend/src/components/compliance/SourceEvidencePanel.jsx` - citation and source detail viewer.
- `frontend/src/components/compliance/ComplianceMemoPanel.jsx` - memo generation controls.
- `frontend/src/components/operations/ServiceHealthGrid.jsx` - service health display.
- `frontend/src/components/operations/DiagnosticExportButton.jsx` - offline diagnostic export.
- `frontend/src/components/evaluations/EvaluationRunTable.jsx` - evaluation results.
- `frontend/src/components/evaluations/EvaluationScoreCard.jsx` - accuracy and citation metrics.

### Frontend Files To Modify

- `frontend/src/App.jsx` - add compliance, operations, and evaluation routes.
- `frontend/src/layouts/MainLayout.jsx` - prioritize Compliance Workspace and Knowledge Library.
- `frontend/src/components/layout/Sidebar.jsx` - simplify navigation around buyer workflow.
- `frontend/src/pages/ChatAssistant.jsx` - remove runtime source rendering bug and align with Policy Q&A.
- `frontend/src/pages/Documents.jsx` - add lifecycle metadata and approval workflow.
- `frontend/src/pages/Users.jsx` - remove hardcoded password and bank ID assumptions.
- `frontend/src/pages/AuditLogs.jsx` - expose AI evidence events clearly.
- `frontend/src/api/axios.js` - handle 401 and 403 auth states consistently.

### Deployment Files To Create

- `deploy/offline/preflight.sh` - environment readiness checks.
- `deploy/offline/package-release.sh` - builds offline release bundle.
- `deploy/offline/install.sh` - installs the appliance from bundle.
- `deploy/offline/upgrade.sh` - upgrades existing appliance.
- `deploy/offline/rollback.sh` - rolls back to previous bundle.
- `deploy/offline/checksums.txt` - generated checksum manifest.
- `docs/appliance/admin-manual.md` - bank IT operations guide.
- `docs/appliance/security-architecture.md` - procurement/security review document.
- `docs/appliance/offline-install-guide.md` - installation instructions.
- `docs/appliance/backup-restore-runbook.md` - backup and recovery.
- `docs/appliance/model-governance.md` - model registry, evaluation, change control.
- `docs/appliance/pilot-playbook.md` - 90-day pilot plan and success metrics.

### Deployment Files To Modify

- `docker-compose.yml` - remove public debug ports by default and add health checks.
- `nginx.conf` - harden headers and proxy settings.
- `.env.example` - remove weak defaults and document airgapped settings.
- `DEPLOYMENT_GUIDE.md` - replace internet-first assumptions with airgapped package flow.
- `PRODUCT_SPECIFICATIONS.md` - remove unproven compliance/SLA/ROI claims.

## Milestone Roadmap

## Milestone 0: Truth Reset And Runtime Discipline

**Goal:** Stop overclaiming and make the existing code testable.

**Exit Criteria:**
- Product docs no longer claim certifications, uptime, ROI, or breach history without proof.
- Backend test environment uses Python 3.10+ or 3.11.
- Frontend build and lint run.
- Backend tests collect and run.
- Generated dependency/build artifacts are ignored by Git.

### Task 0.1: Pin Backend Runtime

**Files:**
- Create: `backend/.python-version`
- Modify: `backend/Dockerfile`
- Modify: `backend/README.md`

- [ ] Add `backend/.python-version` with:

```text
3.11
```

- [ ] Update `backend/Dockerfile` base image to Python 3.11 if it is not already Python 3.10+.
- [ ] Add a backend setup note:

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest -q
```

- [ ] Run:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest -q
```

Expected: tests collect. Failures after collection are acceptable for the next tasks; collection errors are not.

### Task 0.2: Clean Product Claims

**Files:**
- Modify: `PRODUCT_SPECIFICATIONS.md`
- Modify: `README.md`

- [ ] Replace certification claims with "designed to support controls aligned with ..." unless a certificate exists.
- [ ] Remove "zero security breaches", "90% accuracy improvement", and "ROI in 6-12 months" until pilot evidence exists.
- [ ] Replace "24/7 enterprise support included" with actual current support scope or "planned support package."
- [ ] Add an "Evidence Required Before Claiming" section listing certifications, SLA evidence, pilot outcomes, and security test results.

## Milestone 1: Security And Trust Gate

**Goal:** Make every LLM/document path pass the same security and audit controls.

**Exit Criteria:**
- No direct LLM call from request handlers bypasses security policy.
- Every upload endpoint enforces size, extension, and content checks.
- User invite flow does not use hardcoded passwords or bank IDs.
- Auth redirects work for both 401 and 403.
- Tests prove these controls.

### Task 1.1: Shared Upload Policy

**Files:**
- Create: `backend/app/core/upload_limits.py`
- Modify: `backend/app/api/documents.py`
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/api/tasks.py`
- Test: `backend/tests/test_upload_limits.py`

- [ ] Create a shared policy with:

```python
from pathlib import Path
from fastapi import HTTPException, UploadFile

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".xlsx", ".xls", ".pptx", ".ppt"}
ALLOWED_TASK_EXTENSIONS = ALLOWED_DOCUMENT_EXTENSIONS | {".csv"}
DOCUMENT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
TASK_MAX_UPLOAD_BYTES = 20 * 1024 * 1024

def extension_for(filename: str) -> str:
    return Path(filename or "").suffix.lower()

def validate_extension(filename: str, allowed: set[str]) -> str:
    ext = extension_for(filename)
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported")
    return ext

def validate_size(content: bytes, max_bytes: int) -> None:
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {max_bytes // (1024 * 1024)} MB limit")
```

- [ ] Refactor all upload endpoints to use these functions.
- [ ] Add tests for empty file, unsupported extension, over-limit document, and over-limit task upload.
- [ ] Run:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_upload_limits.py -q
```

Expected: all upload policy tests pass.

### Task 1.2: Unified LLM Request Gateway

**Files:**
- Create: `backend/app/services/llm_request_gateway.py`
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/api/tasks.py`
- Modify: `backend/app/services/rag_service.py`
- Test: `backend/tests/test_security_llm_paths.py`

- [ ] Create a gateway function that accepts `raw_message`, `current_user`, `db`, `purpose`, `language`, `active_document_ids`, `session_id`, and optional `file_context`.
- [ ] Gateway order must be:
  1. prompt-injection detection
  2. PII masking
  3. authorization context construction
  4. retrieval with document policy
  5. model call
  6. audit event
- [ ] Refactor `/chat/sessions/{session_id}/messages`, `/stream`, `/stream-file`, and `/tasks/run` to call this gateway or a gateway streaming variant.
- [ ] Add tests proving `/stream-file` rejects prompt injection and masks PII before model input.
- [ ] Run:

```bash
cd backend
env JWT_SECRET=test-secret SUPER_ADMIN_PASSWORD=test-password .venv/bin/python -m pytest tests/test_security_llm_paths.py -q
```

Expected: all security path tests pass.

### Task 1.3: User Invite And Auth Consistency

**Files:**
- Modify: `backend/app/api/users.py`
- Modify: `backend/app/schemas/user.py`
- Modify: `frontend/src/pages/Users.jsx`
- Modify: `frontend/src/api/axios.js`
- Test: `backend/tests/test_users.py`

- [ ] Remove frontend-generated default password and `bank_id: 1`.
- [ ] Backend must assign `bank_id=current_user.bank_id` for bank admins.
- [ ] Backend must accept a temporary password only from authorized admins or generate a one-time reset token.
- [ ] Frontend must redirect to login on both 401 and 403 when unauthenticated/expired.
- [ ] Add tests for bank admin creating a user only in their own bank.
- [ ] Run backend user tests and frontend lint.

## Milestone 2: Document Governance

**Goal:** Make approved knowledge trustworthy and auditable.

**Exit Criteria:**
- Document lifecycle is implemented.
- RAG excludes unapproved/superseded/disabled documents.
- Admin/reviewer can approve, supersede, archive, and disable documents.
- Staff can only access approved documents and own session uploads.

### Task 2.1: Document Lifecycle Schema

**Files:**
- Modify: `backend/app/models/document.py`
- Modify: `backend/app/schemas/document.py`
- Create: `backend/alembic/versions/002_document_governance.py`
- Test: `backend/tests/test_document_policy.py`

- [ ] Add fields:
  - `lifecycle_status: str = "draft"`
  - `effective_date: Optional[datetime]`
  - `expiry_date: Optional[datetime]`
  - `approved_by: Optional[int]`
  - `approved_at: Optional[datetime]`
  - `supersedes_document_id: Optional[int]`
  - `owner_department: Optional[str]`
- [ ] Migration must add nullable columns and backfill existing ready/approved documents safely.
- [ ] Tests must verify default upload starts as draft or uploaded, not approved.

### Task 2.2: Document Policy Service

**Files:**
- Create: `backend/app/services/document_policy_service.py`
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/app/api/documents.py`
- Test: `backend/tests/test_document_policy.py`

- [ ] Implement `can_user_read_document(user, doc, session_id=None)`.
- [ ] Implement `can_document_influence_rag(doc, user, session_id=None)`.
- [ ] Enforce:
  - session uploads only within owner session
  - staff cannot read restricted docs
  - draft/superseded/disabled docs cannot influence normal RAG
  - approved/indexed/ready documents can influence RAG only if lifecycle permits
- [ ] Add tests for staff, bank admin, compliance reviewer, and cross-session attempts.

### Task 2.3: Governance UI

**Files:**
- Modify: `frontend/src/pages/Documents.jsx`
- Create: `frontend/src/components/documents/DocumentLifecycleBadge.jsx`
- Create: `frontend/src/components/documents/DocumentApprovalPanel.jsx`

- [ ] Show lifecycle state on document cards and table rows.
- [ ] Add approve, supersede, archive, disable actions for authorized roles.
- [ ] Require effective date and owner department before approval.
- [ ] Hide lifecycle actions from staff users.
- [ ] Add Playwright coverage for document approval workflow.

## Milestone 3: Source-Backed Compliance Workspace

**Goal:** Replace generic chat as the main buyer workflow.

**Exit Criteria:**
- Compliance Workspace is the first serious product screen.
- User can ask a policy question, inspect source evidence, and export a memo.
- Unsupported answers refuse cleanly instead of hallucinating.

### Task 3.1: Compliance Workspace UI

**Files:**
- Create: `frontend/src/pages/ComplianceWorkspace.jsx`
- Create: `frontend/src/components/compliance/SourceEvidencePanel.jsx`
- Create: `frontend/src/components/compliance/ComplianceMemoPanel.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`

- [ ] Build a dense professional workspace with:
  - question input
  - document scope selector
  - streamed answer area
  - source evidence panel
  - memo panel
  - audit metadata footer
- [ ] Route `/compliance-workspace` to the new page.
- [ ] Make it primary in sidebar navigation.
- [ ] Keep ChatAssistant available as secondary "Session Analysis."

### Task 3.2: Evidence-First Answer Contract

**Files:**
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/app/schemas/chat.py`
- Test: `backend/tests/test_source_backed_answers.py`

- [ ] Define response contract:
  - `answer`
  - `answer_type`: `source_backed`, `not_found`, `general`
  - `sources`
  - `retrieval_query`
  - `model_profile`
  - `limitations`
- [ ] Compliance workspace must default to `source_backed` or `not_found`; no general knowledge fallback.
- [ ] Tests must cover not-found behavior and source presence.

### Task 3.3: Compliance Memo Export

**Files:**
- Modify: `backend/app/api/export.py`
- Modify: `backend/app/services/export_service.py`
- Create: `backend/schemas/export.py`
- Test: `backend/tests/test_compliance_memo_export.py`

- [ ] Add export payload fields:
  - `answer`
  - `sources`
  - `scope`
  - `reviewer`
  - `generated_at`
  - `limitations`
- [ ] PDF/DOCX memo must include source document names, section/page/chunk, and timestamp.
- [ ] Test that export includes citations and does not silently drop source metadata.

## Milestone 4: Evaluation And Model Governance

**Goal:** Replace subjective demo confidence with measurable quality gates.

**Exit Criteria:**
- Admin can run an evaluation set.
- Release candidate must pass minimum thresholds before pilot use.
- Model/retrieval changes are recorded.

### Task 4.1: Evaluation Data Model

**Files:**
- Create: `backend/app/models/evaluation.py`
- Create: `backend/app/schemas/evaluation.py`
- Create: `backend/alembic/versions/003_evaluation_tables.py`

- [ ] Add `EvaluationQuestion` with question, expected answer notes, expected document IDs, expected refusal flag, category, language.
- [ ] Add `EvaluationRun` with model profile, retrieval config, created_by, started_at, completed_at, aggregate scores.
- [ ] Add `EvaluationResult` with answer, sources, correctness score, citation score, refusal score, latency_ms.

### Task 4.2: Evaluation Service

**Files:**
- Create: `backend/app/services/evaluation_service.py`
- Create: `backend/tests/test_evaluation_service.py`

- [ ] Implement deterministic scoring helpers:
  - citation score = expected document IDs present / expected document IDs
  - refusal score = 1 when expected refusal matches actual not_found
  - latency recorded per question
- [ ] Leave human correctness scoring as admin-editable field, not fake automation.
- [ ] Tests must cover citation scoring, refusal scoring, and aggregate scoring.

### Task 4.3: Evaluation Center UI

**Files:**
- Create: `frontend/src/pages/EvaluationCenter.jsx`
- Create: `frontend/src/components/evaluations/EvaluationRunTable.jsx`
- Create: `frontend/src/components/evaluations/EvaluationScoreCard.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] Show latest eval runs and thresholds.
- [ ] Display citation score, refusal score, latency p50/p95, and human correctness.
- [ ] Mark release candidate as blocked if thresholds fail.

## Milestone 5: Appliance Operations

**Goal:** Make the system supportable after installation.

**Exit Criteria:**
- Bank IT can see system health without shell access.
- Vendor can collect offline diagnostics.
- Backup/restore status is visible.

### Task 5.1: Health Service And Operations API

**Files:**
- Create: `backend/app/services/health_service.py`
- Create: `backend/app/api/operations.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_operations.py`

- [ ] Health checks must cover:
  - Postgres
  - Qdrant
  - Redis
  - MinIO or local storage
  - vLLM fast
  - vLLM deep
  - disk free
  - backup freshness
- [ ] Operations endpoints require bank admin or super admin.
- [ ] Diagnostic export must redact secrets from `.env`.

### Task 5.2: Operations Console UI

**Files:**
- Create: `frontend/src/pages/OperationsConsole.jsx`
- Create: `frontend/src/components/operations/ServiceHealthGrid.jsx`
- Create: `frontend/src/components/operations/DiagnosticExportButton.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] Show health cards with status, last check, and operator hint.
- [ ] Show model queue state.
- [ ] Show ingestion failures.
- [ ] Add diagnostic export button.

## Milestone 6: Offline Installer And Upgrade Packaging

**Goal:** Make airgapped deployment repeatable and less founder-dependent.

**Exit Criteria:**
- Release bundle can install without internet.
- Upgrade has rollback.
- Checksums prove bundle integrity.
- Admin docs explain install, backup, restore, and upgrade.

### Task 6.1: Offline Preflight

**Files:**
- Create: `deploy/offline/preflight.sh`
- Test: manual run on target-like Ubuntu host.

- [ ] Check Ubuntu version.
- [ ] Check Docker Compose.
- [ ] Check NVIDIA runtime and `nvidia-smi`.
- [ ] Check required directories.
- [ ] Check ports.
- [ ] Check disk space.
- [ ] Check model paths.
- [ ] Print clear pass/fail summary.

### Task 6.2: Offline Release Bundle

**Files:**
- Create: `deploy/offline/package-release.sh`
- Create: `deploy/offline/install.sh`
- Create: `deploy/offline/upgrade.sh`
- Create: `deploy/offline/rollback.sh`
- Modify: `docker-compose.yml`

- [ ] `package-release.sh` must save Docker images to tar files.
- [ ] Bundle must include compose files, nginx config, migrations, docs, model manifest, checksums.
- [ ] `install.sh` must load images, verify checksums, create directories, write initial `.env`, start services, and run health check.
- [ ] `upgrade.sh` must backup DB, load images, run migrations, restart services, and verify health.
- [ ] `rollback.sh` must restore previous compose/images and DB backup.

### Task 6.3: Appliance Documentation

**Files:**
- Create: `docs/appliance/offline-install-guide.md`
- Create: `docs/appliance/admin-manual.md`
- Create: `docs/appliance/security-architecture.md`
- Create: `docs/appliance/backup-restore-runbook.md`
- Create: `docs/appliance/model-governance.md`
- Create: `docs/appliance/pilot-playbook.md`
- Modify: `DEPLOYMENT_GUIDE.md`

- [ ] Document install flow.
- [ ] Document network ports and no-internet operating mode.
- [ ] Document backup and restore test.
- [ ] Document model registry and change control.
- [ ] Document procurement/security answers honestly.
- [ ] Document pilot success metrics.

## Milestone 7: Pilot Readiness Package

**Goal:** Make the product sellable to one bank pilot without pretending it is mature.

**Exit Criteria:**
- One narrow pilot workflow is documented.
- Success metrics are measurable.
- Buyer packet exists.
- Demo data and scripted walkthrough exist.

### Task 7.1: Pilot Scope

**Files:**
- Create: `docs/appliance/pilot-scope-template.md`

- [ ] Define target users: compliance, risk, policy, audit.
- [ ] Define corpus: approved policies, SOPs, circulars.
- [ ] Define questions: 100 pilot questions.
- [ ] Define success metrics:
  - citation accuracy >= 85% on pilot set
  - refusal correctness >= 90% on unanswerable questions
  - p95 answer latency <= 20 seconds on target hardware
  - zero cross-session or cross-bank source leaks
  - at least 30% time reduction in selected workflow
- [ ] Define exclusions: no automated credit decisioning, no customer-facing advice, no autonomous regulatory filing.

### Task 7.2: Buyer Packet

**Files:**
- Create: `docs/appliance/buyer-packet.md`

- [ ] Include:
  - product one-liner
  - architecture diagram
  - data flow
  - airgapped deployment model
  - security controls
  - role model
  - audit evidence
  - backup/restore
  - support model
  - pilot metrics
  - known limitations

### Task 7.3: Demo Script

**Files:**
- Create: `docs/appliance/demo-script.md`

- [ ] Build demo around one workflow:
  1. compliance officer uploads approved policy and regulatory circular
  2. reviewer approves documents
  3. user asks policy question
  4. answer shows citations
  5. user opens source evidence
  6. user exports memo
  7. admin views audit event
  8. operator views health console

## Release Gates

### Alpha Gate

- Backend tests run on Python 3.10+ or 3.11.
- Frontend build passes.
- Critical security paths tested.
- Existing broad claims removed from docs.

### Pilot Gate

- Document governance works.
- Compliance Workspace works.
- Memo export includes citations.
- Evaluation Center can run at least 50 questions.
- Operations Console shows service health.
- Offline install guide is complete.
- Pilot packet is ready.

### Client-Ready Gate

- Offline installer tested on a clean machine.
- Backup restore tested.
- Evaluation set has at least 100 real/domain questions.
- Security review packet complete.
- Role/document isolation tests pass.
- Support process and SLA are documented truthfully.
- Known limitations are documented.

## 30-Day Execution Plan

### Days 1-3

- Pin Python runtime and make backend tests collect.
- Remove unsupported product claims.
- Fix `.gitignore` and generated artifact hygiene.
- Fix frontend source rendering crash.

### Days 4-7

- Implement shared upload policy.
- Implement unified LLM request gateway.
- Patch `/stream-file` security bypass.
- Remove hardcoded invite password and bank ID.
- Add security regression tests.

### Days 8-12

- Add document lifecycle fields and policy service.
- Update Documents UI for approval workflow.
- Ensure RAG excludes draft/superseded/disabled documents.

### Days 13-17

- Build Compliance Workspace.
- Add source evidence side panel.
- Add evidence-first answer contract.
- Add compliance memo export with citations.

### Days 18-22

- Add evaluation models and service.
- Seed 50 initial evaluation questions.
- Add Evaluation Center UI.
- Establish pilot thresholds.

### Days 23-26

- Add operations health API and UI.
- Add diagnostic export.
- Add backup freshness checks.

### Days 27-30

- Create offline preflight, install, upgrade, rollback scripts.
- Write appliance docs.
- Write buyer packet and pilot scope.
- Run full verification and produce readiness report.

## Commercial Upgrade Plan

### Commercial Thesis

BankAi should not compete as a cheap chatbot or generic enterprise search tool. It should compete as a controlled appliance for banks that have three constraints at once:

1. internal documents cannot be sent to cloud AI tools;
2. staff need faster policy and compliance answers;
3. audit, IT, and risk teams need evidence, access control, and operational ownership.

The initial sale should be a paid pilot, not a broad enterprise rollout. A successful pilot proves accuracy, citation quality, workflow time savings, operational fit, and procurement confidence.

### Positioning

Use:

> BankAi is an airgapped compliance knowledge appliance for banks. It runs inside the bank's own infrastructure, uses local models, answers from approved internal documents, cites exact sources, and keeps audit evidence for every AI interaction.

Avoid:

> AI assistant for banks.

### Packaging

#### Pilot Package

- 90 days
- one department
- one appliance or client-provided server
- 20-50 users
- 500-2,000 documents
- 100-question evaluation set
- fixed pilot success metrics
- vendor-led installation and training
- weekly pilot review with compliance and IT
- final pilot report with accuracy, citation, latency, usage, and workflow findings

#### Production Standard

- one appliance
- compliance/policy/risk users
- annual software/support license
- quarterly health and evaluation review
- offline update packages

#### Production Enterprise

- HA or backup appliance
- multiple departments
- custom workflows
- dedicated support SLA
- deeper integration with bank IAM/SIEM/document repositories

### Pilot Deliverables

The pilot must produce artifacts that make a procurement decision possible:

- installed appliance or client-hosted deployment
- approved pilot corpus
- 100-question evaluation set
- baseline workflow timing before BankAi
- post-pilot workflow timing after BankAi
- citation accuracy report
- refusal correctness report
- latency report on target hardware
- isolation/security test report
- operations health report
- buyer packet updated with actual pilot evidence

### Pricing Direction

Do not sell cheap SaaS seats. Sell appliance + license + support.

- Pilot: paid fixed-scope pilot.
- Production: appliance or client hardware setup fee plus annual license/support.
- Add-ons: HA appliance, custom corpus migration, compliance evaluation pack, SIEM integration, IAM integration, model governance review.

### What Not To Sell Yet

- automated credit decisions
- customer-facing advice
- regulatory filing automation
- autonomous compliance approval
- unrestricted staff-wide chatbot
- generic analytics dashboard
- certification claims
- guaranteed ROI

Those create liability before the product has evidence and controls.

## Risks

### Product Risks

- Banks may see this as an internal IT project rather than a product.
- Generic chat will be ignored if compliance workflow is not sharp.
- Accuracy failures will destroy trust quickly.

### Technical Risks

- Local models may underperform on Nepali, scanned PDFs, or complex policy reasoning.
- Airgapped installs can become custom services unless packaging is disciplined.
- GPU supply, driver issues, and model memory limits can derail pilots.
- RAG quality can degrade as document corpus becomes messy and contradictory.

### Commercial Risks

- Sales cycle may be long.
- Procurement may require certifications the company does not yet have.
- Microsoft/private-cloud incumbents can compete at the platform level.
- Support burden can destroy margins if installs are not repeatable.

## Validation Questions For Buyers

1. Which internal document workflow wastes the most compliance or policy time today?
2. What documents are staff allowed to use as authoritative sources?
3. What happens when staff use outdated circulars or SOPs?
4. Are cloud AI tools permitted for internal bank documents?
5. Who owns approval of AI-generated compliance answers?
6. What evidence would internal audit require?
7. What security documents are required for vendor approval?
8. What hardware and data-center constraints exist?
9. What answer accuracy and citation accuracy would be acceptable for a pilot?
10. What budget would fund this: IT, compliance, risk, or operations?

## Self-Review

- Spec coverage: covers market positioning, client readiness, technical hardening, airgapped packaging, evaluation, operations, docs, pilot readiness, and commercial packaging.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: new service and model names are consistent across task references.
- Scope check: this is a product upgrade portfolio, not a single sprint. It is intentionally split into milestones so each can be executed and verified independently.
