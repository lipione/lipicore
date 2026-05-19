# BankAi Enterprise Intelligence — Implementation Plan

**Date:** 2026-04-28  
**Status:** Active  
**Scope:** Full UI/UX redesign + backend bug fixes + feature completions

---

## 1. Executive Summary

BankAi is being upgraded from a dark-themed fintech MVP into a polished, enterprise-grade
financial intelligence workspace. The design direction shifts from "AI product" to
"High-Stakes Professional Tool" — light, authoritative, document-first.

Two parallel tracks of work:

| Track | Scope |
|---|---|
| **A — Design System Migration** | Entire frontend reimplemented in the Financial Enterprise AI design system |
| **B — Backend Bug Fixes** | 10 critical bugs fixed; session-aware RAG, PII masking, query rewriting added |

---

## 2. Design System Specification

### Token Reference (from `financial_enterprise_ai/DESIGN.md`)

| Token | Value | Usage |
|---|---|---|
| `primary` | `#000000` | Nav background, buttons, headings |
| `primary-container` | `#131b2e` | AI avatar, dark cards, audit table header |
| `secondary` | `#0051d5` | Trust Blue — CTAs, links, focused states |
| `secondary-container` | `#316bf3` | Human message bubble |
| `on-tertiary-container` | `#009668` | Success Green — verified, ready, confidence |
| `tertiary-fixed-dim` | `#4edea3` | Confidence bars, positive indicators |
| `error` | `#ba1a1a` | Critical alerts, stop button |
| `surface` / `background` | `#f8f9ff` | Page background |
| `surface-container-lowest` | `#ffffff` | Cards, panels |
| `outline` | `#76777d` | Secondary text, metadata |
| `on-surface` | `#0b1c30` | Primary text |

### Typography

| Style | Font | Size | Weight |
|---|---|---|---|
| h1 | Public Sans | 36px | 700 |
| h2 | Public Sans | 24px | 600 |
| body-md | Inter | 16px | 400 |
| body-sm | Inter | 14px | 400 |
| label-caps | Inter | 12px | 600, tracking 0.05em |
| nepali-supplement | Inter | 110% | 400, lh 1.8 |

### Shapes

- Standard elements: `rounded` = 2px (0.125rem)
- Large containers: `rounded-lg` = 4px (0.25rem)
- Larger cards: `rounded-xl` = 8px (0.5rem)
- Chips/pills: `rounded-full`

### Elevation (tonal, no heavy shadows)

- Level 0: `bg-surface` page base
- Level 1: `bg-white border border-slate-200` — cards
- Level 2: `shadow-sm` for floating elements (dropdowns, modals)

---

## 3. Page Inventory

| Page | Route | Design Source | Priority |
|---|---|---|---|
| Login | `/login` | Custom | P0 |
| Dashboard | `/dashboard` | `dashboard/code.html` | P0 |
| Chat Interface | `/chat` | `chat_interface/code.html` | P0 |
| Document Library | `/documents` | `document_library/code.html` | P0 |
| Audit Log Forensics | `/audit-logs` | `audit_log_forensics/code.html` | P1 |
| Session History | `/sessions` | `session_history/code.html` | P1 |
| Analytics | `/analytics` | `analytics_dashboard/code.html` | P1 |
| User Roles & Permissions | `/users` | `user_roles_permissions/code.html` | P1 |
| Account Settings | `/settings` | `account_settings/code.html` | P2 |
| Admin Security | `/admin/security` | `admin_security/code.html` | P2 |
| Help Center | `/help` | `help_center/code.html` | P2 |
| Compliance Risk | `/compliance` | `compliance_risk_assessment/code.html` | P2 |

---

## 4. Shared Layout Architecture

```
App.jsx
└── MainLayout.jsx
    ├── Sidebar.jsx (fixed, w-64, bg-slate-50, border-r)
    │   ├── BankAi logo + "Enterprise AI" wordmark
    │   ├── "Upload Document" primary CTA button
    │   ├── Nav links (New Chat, Session History, Document Library, Analytics)
    │   └── Footer links (Security Status, Help Center)
    └── ContentArea
        ├── TopBar.jsx (fixed h-16, bg-white border-b)
        │   ├── "BankAi" wordmark + top nav tabs (Audit Log, Analysis, Compliance)
        │   ├── Bilingual switcher (EN | ने)
        │   ├── Icons: encryption lock, notifications, settings
        │   └── User avatar
        └── <Outlet /> (page content)
```

---

## 5. Component Library

### New/Updated Components

| Component | File | Description |
|---|---|---|
| `Sidebar` | `components/layout/Sidebar.jsx` | Fixed sidebar with active state |
| `TopBar` | `components/layout/TopBar.jsx` | Fixed header with bilingual toggle |
| `MainLayout` | `layouts/MainLayout.jsx` | Combines Sidebar + TopBar |
| `StatCard` | `components/ui/StatCard.jsx` | KPI card with left-border accent |
| `DocumentCard` | `components/ui/DocumentCard.jsx` | Library doc card with status badge |
| `SessionRow` | `components/ui/SessionRow.jsx` | Session table row with confidence bar |
| `SourceChip` | `components/chat/SourceChip.jsx` | Inline source reference chip |
| `ConfidenceBadge` | `components/chat/ConfidenceBadge.jsx` | Color-coded AI confidence score |
| `FileUploadBento` | `components/chat/FileUploadBento.jsx` | Upload zone + active file bento grid |
| `AnalysisContextPanel` | `components/chat/AnalysisContextPanel.jsx` | Right panel in chat view |
| `AuditDetailPanel` | `components/audit/AuditDetailPanel.jsx` | Audit log action details side panel |
| `StatusBadge` | `components/ui/StatusBadge.jsx` | Semantic color badges (VERIFIED, CRITICAL, etc) |

---

## 6. Backend Bug Fix Register

| # | Bug | Severity | File | Fix |
|---|---|---|---|---|
| B1 | `upload_points(points, doc.bank_id)` — extra arg crashes indexing | **CRITICAL** | `ingestion_service.py:135`, `qdrant_service.py:35` | Remove `doc.bank_id` from call site |
| B2 | Session-aware RAG doesn't prioritize active session docs | **HIGH** | `chat.py:207`, `qdrant_service.py:41` | Add session_id filter to `search_points`; search active docs first |
| B3 | Active documents reset to `[]` on session reload | **HIGH** | `ChatAssistant.jsx:75` | Fetch `active_document_ids_json` from session API on `loadSession()` |
| B4 | `stream-file` deletes temp file — never indexed | **HIGH** | `chat.py:441` | Use same `files` endpoint flow; keep file, index asynchronously |
| B5 | No SSE status events before first token | **MEDIUM** | `chat.py:247` | Yield `{"type":"status","message":"..."}` events before LLM call |
| B6 | Regenerate only fills input, doesn't call API | **MEDIUM** | `ChatAssistant.jsx:149` | Call stream endpoint with same context |
| B7 | Source field `title` vs `document_title` mismatch | **MEDIUM** | `rag_service.py:84`, `SourceCards.jsx` | Normalize to `document_title` everywhere |
| B8 | LLM told not to use markdown, but renderer expects it | **LOW** | `rag_service.py:13` | Remove anti-markdown instruction |
| B9 | FilePreviewCard SSE no auth header | **LOW** | `FilePreviewCard.jsx:34` | Accept polling fallback; add token to query param |
| B10 | Edit-and-resend missing entirely | **MEDIUM** | `ChatAssistant.jsx` | Add edit button on user messages |

---

## 7. New Feature Register

| # | Feature | Priority | Files |
|---|---|---|---|
| F1 | Query rewrite service for follow-up questions | P0 | `services/query_rewrite_service.py` |
| F2 | Session-aware RAG with priority ordering | P0 | `qdrant_service.py`, `chat.py` |
| F3 | Session active documents restored on reload | P0 | `ChatAssistant.jsx`, `chat.py` |
| F4 | SSE status events (thinking/working messages) | P1 | `chat.py` |
| F5 | Expanded PII masking (Nepal phone, email, account#) | P1 | `guardrail_service.py` |
| F6 | Real Analytics aggregates endpoint | P2 | `api/analytics.py` |
| F7 | Session summary auto-update | P2 | `chat.py`, `ChatSession` model |

---

## 8. File Change Map

### Frontend — New/Modified

```
frontend/src/
├── index.css                          ← Google Fonts import, base styles
├── App.jsx                            ← Add new routes
├── layouts/
│   └── MainLayout.jsx                 ← REWRITE (new design)
├── components/
│   ├── layout/
│   │   ├── Sidebar.jsx                ← NEW
│   │   └── TopBar.jsx                 ← NEW
│   ├── ui/
│   │   ├── StatCard.jsx               ← NEW
│   │   ├── DocumentCard.jsx           ← NEW
│   │   ├── StatusBadge.jsx            ← NEW
│   │   └── ConfidenceBadge.jsx        ← NEW
│   └── chat/
│       ├── FilePreviewCard.jsx        ← UPDATE (auth fix, new design)
│       ├── SourceCards.jsx            ← UPDATE (new design, field fix)
│       ├── FileUploadBento.jsx        ← NEW
│       └── AnalysisContextPanel.jsx   ← NEW
├── pages/
│   ├── Login.jsx                      ← UPDATE (new design)
│   ├── Dashboard.jsx                  ← REWRITE (real data + new design)
│   ├── ChatAssistant.jsx              ← REWRITE (session fix + new design)
│   ├── Documents.jsx                  ← REWRITE (bento grid + preview panel)
│   ├── AuditLogs.jsx                  ← REWRITE (forensics design + detail panel)
│   ├── SessionHistory.jsx             ← NEW
│   ├── Analytics.jsx                  ← NEW
│   ├── Users.jsx                      ← UPDATE (roles/permissions design)
│   ├── Settings.jsx                   ← REWRITE (account settings design)
│   ├── AdminSecurity.jsx              ← NEW
│   └── HelpCenter.jsx                 ← NEW
└── api/
    └── axios.js                       ← keep as-is
```

### Backend — Modified

```
backend/app/
├── services/
│   ├── ingestion_service.py           ← Fix upload_points call (B1)
│   ├── qdrant_service.py              ← Add session_id filter (B2)
│   ├── rag_service.py                 ← Fix markdown instruction (B8), source fields (B7)
│   ├── guardrail_service.py           ← Expand PII patterns (F5)
│   └── query_rewrite_service.py       ← NEW (F1)
├── api/
│   ├── chat.py                        ← Fix B2/B4/B5; add query rewrite; status SSE
│   └── analytics.py                   ← NEW (F6)
└── main.py                            ← Register analytics router
```

---

## 9. Chat Flow (Fixed)

```
User sends message
    ↓
1. Auth + session load
2. Verify user owns session + same bank
3. PII mask user question
4. Prompt injection check
5. Save user message to DB
6. Load last 10 messages (history)
7. Load session.active_document_ids_json
8. Detect if follow-up question
9. Rewrite query via query_rewrite_service (if follow-up)
10. SSE: yield {"type":"status","message":"Searching your uploaded documents..."}
11. RAG Priority 1: search active session docs (session_id + active doc IDs)
12. RAG Priority 2: search global bank knowledge (bank_id, status=approved)
13. SSE: yield {"type":"status","message":"Preparing source-based answer..."}
14. Build prompt (system + history + context)
15. Stream LLM response token by token
16. SSE: yield {"type":"done", "sources":[...], "suggestions":[...]}
17. Save assistant message with sources + suggestions
18. Save audit log
19. Update session title if first message
```

---

## 10. RAG Priority (Fixed)

```python
# Priority 1 — Active session uploads
search_points(
    query_vector,
    bank_id=current_user.bank_id,
    session_id=session_id,
    document_ids=active_document_ids,   # from session.active_document_ids_json
    limit=5
)

# Priority 2 — Global bank knowledge
search_points(
    query_vector,
    bank_id=current_user.bank_id,
    document_scope="global_knowledge",
    status="approved",
    limit=3
)

# Merge: session results first, then fill remaining slots from global
```

---

## 11. Document Upload Flow (Fixed)

```
User selects file in chat
    ↓
1. Frontend shows file card with status=uploading
2. POST /api/chat/sessions/{id}/files
3. Backend saves file to disk
4. Creates Document record (session_id, scope=session_upload)
5. Adds doc.id to session.active_document_ids_json
6. Returns {document_id, status: "uploaded"}
7. Frontend updates file card; starts SSE polling for status
8. BackgroundTask: extract → chunk → embed → index → status=ready
9. SSE stream updates file card progress bar
10. File card shows "Ready for questions" when status=ready
```

---

## 12. PII Patterns (Expanded)

| Pattern | Replacement |
|---|---|
| `\d{3}-\d{2}-\d{4}` | `[REDACTED SSN]` |
| 16-digit card pattern | `[REDACTED CC]` |
| Nepal mobile: `\b9[6-9]\d{8}\b` | `[REDACTED PHONE]` |
| Email: `[\w.+-]+@[\w-]+\.[a-z]{2,}` | `[REDACTED EMAIL]` |
| Account-like: `\b[A-Z]{2,4}\d{8,16}\b` | `[REDACTED ACCOUNT]` |
| DOB labels: `DOB\s*[:=]\s*\d{2}[/-]\d{2}[/-]\d{4}` | `DOB: [REDACTED]` |
| Citizenship no: `\b\d{2}-\d{2}-\d{2}-\d{5}\b` | `[REDACTED CITIZENSHIP]` |
| Passport: `\b[A-Z]{2}\d{7}\b` | `[REDACTED PASSPORT]` |
| PAN/VAT: `\b\d{9}\b` (9 digits) | `[REDACTED PAN]` |

---

## 13. Acceptance Criteria

- [ ] Login page uses new enterprise light design
- [ ] Dashboard shows real session count, real doc count from backend
- [ ] Chat works with session-aware RAG (active docs prioritized)
- [ ] Follow-up questions use query rewrite service
- [ ] Active docs restored on browser refresh
- [ ] Upload progress bar accurate
- [ ] Document processing status updates in real time
- [ ] Streaming shows status events before first token
- [ ] Stop generation cancels SSE stream
- [ ] Regenerate calls API (not just fills input)
- [ ] Edit and resend available on user messages
- [ ] Source chips show document title + page number
- [ ] PII masking covers Nepal phone, email, account numbers
- [ ] Audit log page shows real data with detail panel
- [ ] Document Library shows bento grid with preview panel
- [ ] Analytics page shows real counts (or empty state if no data)
- [ ] User Roles page lists users with role badges
- [ ] All pages use Financial Enterprise AI design tokens
- [ ] No cross-bank or cross-session document leakage
- [ ] `upload_points` crash fixed — documents index successfully

---

## 14. Sprint Breakdown

### Sprint 1 (Now) — Foundation + Core Chat Fix
- Design system tokens into Tailwind config
- Shared layout: Sidebar + TopBar
- Login page
- Dashboard page
- Chat Interface (full redesign + all bug fixes)
- Backend: B1, B2, B3, B4, B5, B6, B7, B8 fixes

### Sprint 2 — Document & Audit Pages
- Document Library with bento grid + preview panel
- Audit Log Forensics with detail panel
- Session History page
- Backend: query rewrite service (F1)

### Sprint 3 — Admin & Analytics
- Analytics page with real data
- User Roles & Permissions page
- Account Settings + Admin Security
- Help Center
- Backend: analytics endpoint (F6), expanded PII (F5)

---

## 15. Known Limitations

1. No refresh tokens — JWT expires after 8h, requires re-login
2. MinIO configured but files stored on disk — production should use MinIO
3. No Alembic migrations — schema managed by SQLModel `create_all`
4. Local vLLM model servers must be running and reachable from the backend
5. Scanned PDF OCR uses vision LLM (not pytesseract) — quality depends on model
6. No WebSocket — SSE only (no bidirectional events)
7. Session summary auto-update not yet implemented

---

*Plan last updated: 2026-04-28*
