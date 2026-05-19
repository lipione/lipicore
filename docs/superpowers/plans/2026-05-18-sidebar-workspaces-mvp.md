# Sidebar Workspaces MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete each BankAi sidebar page as a useful bank-ready MVP workspace.

**Architecture:** Keep the current React/Vite and FastAPI stack. Use existing frontend API client calls and derive MVP metrics client-side where backend-specific endpoints are not available yet. Add only one new frontend page for Reports and keep changes closely scoped.

**Tech Stack:** React, Vite, Tailwind CSS, FastAPI APIs, existing export endpoint, ESLint, route/link static verification.

---

### Task 1: Reports Workspace

**Files:**
- Create: `frontend/src/pages/Reports.jsx`
- Modify: `frontend/src/App.jsx`

- [ ] Add a separate Reports page that fetches analytics, documents, audit logs, and users.
- [ ] Generate four practical report types: usage, audit activity, document inventory, and AI quality.
- [ ] Support TXT/PDF/DOCX export through `/api/export`.
- [ ] Route `/reports` to `Reports` instead of `Analytics`.

### Task 2: Compliance Monitor

**Files:**
- Modify: `frontend/src/pages/ComplianceRisk.jsx`

- [ ] Replace static fiction metrics with derived metrics from analytics, documents, audit logs, and users.
- [ ] Add review queue items from failed documents and high-risk audit metadata.
- [ ] Add CSV export for the visible compliance snapshot.
- [ ] Keep clear empty states when no data exists.

### Task 3: Users & Roles

**Files:**
- Modify: `frontend/src/pages/Users.jsx`

- [ ] Remove hidden `BankAi@2024!` user password.
- [ ] Remove hardcoded `bank_id: 1`.
- [ ] Add visible temporary password field and generator.
- [ ] Disable users through the existing backend endpoint instead of calling a missing delete endpoint.
- [ ] Add CSV export for the current users list.

### Task 4: Help Center

**Files:**
- Modify: `frontend/src/pages/HelpCenter.jsx`

- [ ] Replace generic support articles with practical BankAi usage guidance.
- [ ] Add citation, document governance, roles, reporting, and limitations guidance.
- [ ] Use branding support contact where available.
- [ ] Avoid dead buttons.

### Task 5: Page Integrity Checks

**Files:**
- No production file changes expected.

- [ ] Run stale reference and dead-link scan.
- [ ] Run route/link static verifier.
- [ ] Run frontend build.
- [ ] Run frontend lint.
