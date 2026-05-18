# AI Trust Product Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make BankAi feel safer and more useful for bank staff by surfacing citation support, source passages, ingestion readiness, evaluation results, and guided task execution.

**Architecture:** Keep the current FastAPI and React/Vite stack. Reuse existing backend endpoints for chat, documents, tasks, analytics, and RAG evaluations. Add focused frontend components and route wiring instead of new backend tables.

**Tech Stack:** React, Vite, Tailwind, FastAPI APIs, existing RAG evaluation endpoint.

---

### Task 1: Citation Trust And Source Evidence

**Files:**
- Modify: `frontend/src/components/chat/AnswerTrustBadge.jsx`
- Modify: `frontend/src/components/chat/SourceEvidencePanel.jsx`
- Modify: `frontend/src/pages/ChatAssistant.jsx`

- [ ] Add citation verification states for verified, partially supported, unsupported, and no-source answers.
- [ ] Show exact source passage text with page/section/chunk metadata.
- [ ] Preserve source-level verification metadata when reloading old chat sessions.

### Task 2: Chat Session Persistence

**Files:**
- Modify: `frontend/src/pages/ChatAssistant.jsx`

- [ ] Always reopen the most recent valid session unless the URL explicitly names a session.
- [ ] Track the active session after a new message, new session, and manual session load.
- [ ] Avoid clearing active chat context until the user chooses a new chat.

### Task 3: Document Ingestion Clarity

**Files:**
- Modify: `frontend/src/pages/Documents.jsx`

- [ ] Add explicit processing stages: uploaded, extracting text/OCR, chunking, embedding, indexing, ready, approved, failed.
- [ ] Show progress, ready-for-chat state, failure reason, scope, department, and lifecycle metadata.
- [ ] Make failed/processing/ready states visually scannable for bank operators.

### Task 4: RAG Evaluation Center

**Files:**
- Create: `frontend/src/pages/EvaluationCenter.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/config/rolePermissions.js`

- [ ] Add admin/auditor-visible evaluation route.
- [ ] Let admins paste/edit JSON evaluation cases.
- [ ] Run `POST /api/evaluations/rag`.
- [ ] Display pass rate, source recall, citation recall, answer recall, failed cases, and source evidence.

### Task 5: AI Tasks UX Polish

**Files:**
- Modify: `frontend/src/pages/Tasks.jsx`

- [ ] Make the current guided flow more explicit and staff-friendly.
- [ ] Add prompt-quality checklist and output-readiness panel.
- [ ] Keep export/edit/re-run controls visible after generation.

### Task 6: Model Capacity Clarity

**Files:**
- Modify: `frontend/src/pages/Analytics.jsx`

- [ ] Add plain operational interpretation for active, waiting, limits, and slot usage.
- [ ] Separate measured capacity evidence from live status.
- [ ] Warn that streaming bursts have higher tail latency.

### Verification

- [ ] Run `npm run build` in `frontend`.
- [ ] Run `npm run lint` in `frontend`.
- [ ] Deploy frontend changes to the remote test server.
- [ ] Run `./deploy/upgrade.sh --check-only` remotely.
- [ ] Check public `/health`, `/chat`, `/documents`, `/tasks`, `/analytics`, and `/evaluations`.
