# Sidebar Workspaces MVP Design

## Goal
Complete every sidebar destination as a usable bank staff workspace, backed by existing APIs where available, with no dead links, empty sections, or hidden demo credentials.

## Product Direction
BankAi should feel like a private bank GPT appliance with operational workspaces around it. The sidebar sections must not be marketing pages. Each page should let staff or admins do a concrete job: ask, retrieve, govern, review, report, audit, manage users, or get support.

## Scope
- Chat Assistant remains the main staff AI workspace with modes, source evidence, and trust states.
- Process Navigator remains a curated, configurable SOP browser for MVP, with strong search/filter/detail behavior.
- Document Library remains the knowledge governance surface for upload, status, approval, selection, and chat handoff.
- Compliance Monitor becomes a data-backed review dashboard using analytics, audit, document, and user data.
- Analytics stays focused on adoption and system usage.
- Reports becomes a separate report-generation/export workspace, not an alias to Analytics.
- AI Tasks remains template-driven task execution.
- Audit Logs remains the review and CSV export surface for governance evidence.
- Users & Roles must remove hidden hardcoded password and bank ID assumptions.
- Settings remains white-label, account, notification, and API-key configuration.
- Help Center becomes practical product support and limitation guidance.

## Non-Goals
- Full enterprise workflow engine.
- Real regulator integration.
- SSO/MFA implementation.
- Persistent report history.
- Dynamic Process Navigator backend storage.

## Data Sources
- `/api/analytics/summary`
- `/api/documents`
- `/api/audit`
- `/api/users`
- `/api/tasks/templates`
- `/api/export`
- `/api/configuration/branding`

## UX Requirements
- Every page has a clear title, purpose, primary action, empty state, and error-safe rendering.
- Report and compliance pages must label derived metrics clearly.
- Frontend must not silently create users with a shared password.
- Frontend must not assume `bank_id: 1`; it should use the current user bank when available.
- Dead `href="#"` links are not allowed.

## Acceptance Criteria
- Sidebar route/link static check passes.
- Frontend build passes.
- Frontend lint has no errors.
- Reports route renders independently from Analytics.
- Compliance route uses live data when available and explicit empty states otherwise.
- User creation form requires a visible temporary password or generated password.
- No frontend references to Ollama, port 11434, bad `/v1/v1`, or empty anchors.
