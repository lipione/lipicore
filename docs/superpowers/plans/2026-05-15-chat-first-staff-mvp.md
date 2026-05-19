# Chat-First Staff MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make BankAi feel like a usable GPT-style assistant for all bank staff by adding chat modes, answer trust, source evidence, and onboarding prompts.

**Architecture:** Keep the existing FastAPI streaming chat and React chat page. Add a small backend mode/trust helper contract and frontend components that consume mode, source, and answer metadata without changing the database schema.

**Tech Stack:** FastAPI, Pydantic, SQLModel, pytest, React, Vite, Tailwind CSS.

---

### Task 1: Backend Mode And Trust Contract

**Files:**
- Modify: `backend/app/schemas/chat.py`
- Modify: `backend/app/api/chat.py`
- Create: `backend/tests/test_chat_modes.py`

- [ ] Add `mode` to `ChatRequest` with the allowed values `ask_knowledge`, `analyze_file`, `summarize`, `draft`, `translate`, and `compare`.
- [ ] Add helper functions in `chat.py`:
  - `mode_instruction(mode)`
  - `derive_answer_metadata(mode, sources, active_document_ids, answer)`
- [ ] Add tests proving default mode, invalid mode rejection, trust derivation, and mode prompt text.
- [ ] Run `pytest backend/tests/test_chat_modes.py -q`.

### Task 2: Backend Streaming Metadata

**Files:**
- Modify: `backend/app/api/chat.py`

- [ ] Append the mode instruction to the system prompt for streaming and non-streaming chat.
- [ ] Include `answer_metadata` in the final streaming `done` event.
- [ ] Include answer metadata in audit metadata for both streaming and non-streaming paths.
- [ ] Run backend tests.

### Task 3: Frontend Chat UX Components

**Files:**
- Create: `frontend/src/components/chat/ChatModeSelector.jsx`
- Create: `frontend/src/components/chat/AnswerTrustBadge.jsx`
- Create: `frontend/src/components/chat/SourceEvidencePanel.jsx`

- [ ] Build a compact mode selector using the current branding `allowed_modes`.
- [ ] Build answer trust badges for the five trust states.
- [ ] Build a source evidence panel that renders source title, section/page/chunk, snippet, and source count.

### Task 4: Chat Page Integration

**Files:**
- Modify: `frontend/src/pages/ChatAssistant.jsx`

- [ ] Track `selectedMode`.
- [ ] Send `mode` in stream requests.
- [ ] Parse `answer_metadata` from the final stream event.
- [ ] Show prompt chips when the chat has only the welcome message.
- [ ] Show trust badges above assistant messages.
- [ ] Replace fragile inline source chip logic with the new source evidence component.
- [ ] Run frontend lint/build.

### Task 5: Verify And Deploy

**Files:**
- Remote deployment under `/data/bankai`

- [ ] Run backend tests.
- [ ] Run frontend build and lint.
- [ ] Package changed files.
- [ ] Copy to remote.
- [ ] Rebuild and restart backend/frontend/nginx.
- [ ] Verify public `/admin/settings`, `/chat`, and `/api/config/branding`.
