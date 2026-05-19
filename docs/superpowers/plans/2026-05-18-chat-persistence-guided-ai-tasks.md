# Chat Persistence and Guided AI Tasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Chat Assistant resume the last active conversation unless the user explicitly starts a new chat, and convert AI Tasks into a guided step-by-step workflow for bank staff.

**Architecture:** Chat persistence is handled in `ChatAssistant.jsx` with localStorage plus server session validation. AI Tasks remains a single page using the existing `/tasks/templates` and `/tasks/run` APIs, but its UI changes from a modal form to a wizard with task discovery, input/upload, prompt review, generation, and export.

**Tech Stack:** React, Vite, existing Axios API client, existing Tailwind/material-symbols styling.

---

### Task 1: Persist Chat Session Selection

**Files:**
- Modify: `frontend/src/pages/ChatAssistant.jsx`

- [ ] Add a `LAST_CHAT_SESSION_KEY` constant.
- [ ] Save the active session ID whenever a session is loaded or created.
- [ ] On `/chat` without a `session` query parameter, load localStorage session if it still exists; otherwise load the newest server session; only create a session when none exist.
- [ ] Keep URL and state in sync.

### Task 2: Guided AI Tasks Wizard

**Files:**
- Replace: `frontend/src/pages/Tasks.jsx`

- [ ] Replace the modal-centric grid with a persistent workspace layout.
- [ ] Add steps: choose task, add source, improve prompt, generate, review/export.
- [ ] Add prompt-building helpers per task type.
- [ ] Keep existing `/tasks/run` API payload unchanged.
- [ ] Preserve export support.

### Task 3: Verification

- [ ] Run `npm run build` in `frontend`.
- [ ] Run `npm run lint` in `frontend`.
- [ ] Run `git diff --check` on changed files.
