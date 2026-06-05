# Internal Banking Workspace Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade LipiCore from a source-backed bank AI assistant into a daily internal banking workspace with Super Admin feature controls, employee search, CEO messages, notifications, alerts, forex/exchange-rate utilities, banking time/date tools, staff work queues, policy-change operations, knowledge-gap tracking, and banking workflow copilots.

**Architecture:** Add small, bank-scoped workflow modules that reuse the current FastAPI, SQLModel, PostgreSQL, audit, RAG, Redis/RQ, and React workspace patterns. Every new module must be controlled by a Super Admin feature flag per bank; disabled modules are hidden in the UI and rejected by backend API guards. Keep Qdrant for approved document retrieval only; do not index private employee or messenger content into RAG in this phase.

**Tech Stack:** FastAPI, SQLModel, Alembic, PostgreSQL/SQLite tests, React/Vite, Tailwind, existing Messenger API, existing RAG/evaluation services.

---

## Product Boundary

These features help employees prepare, find, draft, track, and review internal banking work. They must not approve loans, make compliance decisions, verify signatures/seals, make AML decisions, execute forex trades, set customer exchange rates without the bank's approved source, or bypass human review.

## Release Sequence

0. **Foundation: Super Admin Feature Controls**
   - Super Admin can enable/disable every new module per bank.
   - Disabled modules disappear from navigation and dashboards.
   - Backend APIs return `403 feature_disabled` for disabled modules.
   - Toggle changes are audited.

1. **Release 1: Employee Directory + Expert Finder**
   - Search active employees by name, email, role, department, branch, title, expertise tags, and escalation areas.
   - Connect results to Staff Messenger direct messages.
   - Keep all results bank-scoped.
   - Add a small Market And Time utility page for bank-published forex rate batches, branch/world clocks, date display, and banking cutoff reminders.

2. **Release 2: Staff Daily Inbox + Notifications**
   - Unified work queue for document reviews, policy changes, complaint drafts, long-document analysis jobs, knowledge gaps, and assigned follow-ups.
   - Shows priority, due date, owner, status, and source links.
   - Adds bank-scoped notifications and actionable alerts for assigned work, policy changes, approvals, long-document job completion, and risk events.

3. **Release 3: CEO Message Center + Policy Change Digest + Knowledge Gap Dashboard**
   - Bank admins or authorized communication owners can publish CEO messages to all staff, departments, branches, or roles.
   - Important CEO messages create notifications and optional acknowledgement tasks.
   - Compare new/updated policies against previous versions.
   - Generate department impact, staff action items, and acknowledgement tasks.
   - Track unanswered/not-found questions as document or policy gaps.

4. **Release 4: Banking Workflow Copilots**
   - Complaint/dispute workspace.
   - Circular impact analyzer.
   - Branch/customer-care response builder.
   - KYC/AML case prep assistant.
   - Document checklist validator.

## Shared File Structure

- Modify `backend/app/models/user.py`: keep base user fields; add relationships only if needed.
- Create `backend/app/models/employee_profile.py`: employee profile, branch/title/extension/expertise/escalation fields.
- Create `backend/app/models/feature_flag.py`: bank-level feature flags controlled by Super Admin.
- Create `backend/app/models/staff_work_item.py`: shared daily inbox/work queue table.
- Create `backend/app/models/notification.py`: notifications, alert preferences, read state, and alert severity.
- Create `backend/app/models/ceo_message.py`: CEO message publishing, audience targeting, acknowledgement state.
- Create `backend/app/models/market_utility.py`: bank-published exchange-rate batches, rate rows, source metadata, and banking calendar events.
- Create `backend/app/models/policy_change.py`: policy digest, acknowledgements, and affected department records.
- Create `backend/app/models/knowledge_gap.py`: not-found and weak-source question tracking.
- Create `backend/app/models/complaint_workspace.py`: complaint/dispute cases if existing `support_case` is not enough.
- Create `backend/app/models/checklist_workspace.py`: document checklist templates and validation results.
- Create `backend/app/schemas/employee_directory.py`
- Create `backend/app/schemas/feature_flag.py`
- Create `backend/app/schemas/staff_work_item.py`
- Create `backend/app/schemas/notification.py`
- Create `backend/app/schemas/ceo_message.py`
- Create `backend/app/schemas/market_utility.py`
- Create `backend/app/schemas/policy_change.py`
- Create `backend/app/schemas/knowledge_gap.py`
- Create `backend/app/schemas/complaint_workspace.py`
- Create `backend/app/schemas/checklist_workspace.py`
- Create `backend/app/services/employee_directory_service.py`
- Create `backend/app/services/feature_flag_service.py`
- Create `backend/app/services/staff_work_item_service.py`
- Create `backend/app/services/notification_service.py`
- Create `backend/app/services/ceo_message_service.py`
- Create `backend/app/services/market_utility_service.py`
- Create `backend/app/services/policy_change_service.py`
- Create `backend/app/services/knowledge_gap_service.py`
- Create `backend/app/services/complaint_workspace_service.py`
- Create `backend/app/services/checklist_workspace_service.py`
- Create `backend/app/api/employee_directory.py`
- Create `backend/app/api/feature_flags.py`
- Create `backend/app/api/staff_work_items.py`
- Create `backend/app/api/notifications.py`
- Create `backend/app/api/ceo_messages.py`
- Create `backend/app/api/market_utilities.py`
- Create `backend/app/api/policy_changes.py`
- Create `backend/app/api/knowledge_gaps.py`
- Create `backend/app/api/complaint_workspace.py`
- Create `backend/app/api/checklist_workspace.py`
- Modify `backend/app/main.py`: include new routers under `/api`.
- Add Alembic migrations beginning with `014`.
- Create backend tests for each service/API.
- Create `frontend/src/contexts/FeatureFlagContext.jsx`
- Create `frontend/src/pages/SuperAdminFeatureControls.jsx`
- Create `frontend/src/pages/EmployeeDirectory.jsx`
- Create `frontend/src/pages/StaffInbox.jsx`
- Create `frontend/src/pages/Notifications.jsx`
- Create `frontend/src/pages/CeoMessages.jsx`
- Create `frontend/src/pages/MarketAndTime.jsx`
- Create `frontend/src/pages/PolicyChangeCenter.jsx`
- Create `frontend/src/pages/KnowledgeGaps.jsx`
- Create or extend workflow pages for complaints, circular impact, KYC prep, and checklist validation.
- Modify `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`, and `frontend/src/config/rolePermissions.js`.

---

## Task 0: Super Admin Feature Controls

**Files:**
- Create: `backend/app/models/feature_flag.py`
- Create: `backend/alembic/versions/014_feature_flags.py`
- Create: `backend/app/schemas/feature_flag.py`
- Create: `backend/app/services/feature_flag_service.py`
- Create: `backend/app/api/feature_flags.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/contexts/FeatureFlagContext.jsx`
- Create: `frontend/src/pages/SuperAdminFeatureControls.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/components/lipicore/PermissionGate.jsx`
- Test: `backend/tests/test_feature_flags.py`

- [ ] **Step 1: Define feature keys**

Feature keys:

```text
employee_directory
market_time
staff_inbox
notifications
ceo_messages
knowledge_gaps
policy_changes
audit_evidence_pack
complaint_workspace
circular_impact_analyzer
branch_response_builder
kyc_case_prep
checklist_validator
```

Existing core features may also be exposed later:

```text
chat
documents
ocr_extraction
evaluations
model_lab
messenger
process_navigator
analytics
reports
```

- [ ] **Step 2: Add feature flag model**

`BankFeatureFlag` fields:

- `id`
- `bank_id`
- `feature_key`
- `enabled`
- `configured_by_user_id`
- `reason`
- `metadata_json`
- `created_at`
- `updated_at`

Add a unique constraint on `(bank_id, feature_key)`.

- [ ] **Step 3: Add service**

`feature_flag_service.py` should provide:

```python
DEFAULT_NEW_FEATURE_FLAGS = {
    "employee_directory": False,
    "market_time": False,
    "staff_inbox": False,
    "notifications": False,
    "ceo_messages": False,
    "knowledge_gaps": False,
    "policy_changes": False,
    "audit_evidence_pack": False,
    "complaint_workspace": False,
    "circular_impact_analyzer": False,
    "branch_response_builder": False,
    "kyc_case_prep": False,
    "checklist_validator": False,
}
```

New modules default to disabled until Super Admin enables them for a bank. Existing core features keep their current behavior unless explicitly added to the flag table later.

Functions:

- `list_feature_flags(db, bank_id)`
- `is_feature_enabled(db, bank_id, feature_key)`
- `set_feature_flag(db, bank_id, feature_key, enabled, configured_by_user_id, reason=None)`
- `require_feature_enabled(db, bank_id, feature_key)`

`require_feature_enabled` raises `HTTPException(status_code=403, detail={"code": "feature_disabled", "feature": feature_key})`.

- [ ] **Step 4: Add API**

Endpoints:

```text
GET /api/feature-flags?bank_id=
PATCH /api/feature-flags/{bank_id}/{feature_key}
```

Rules:

- only `super_admin` can update flags;
- `bank_admin` can read their bank flags but cannot change them;
- `super_admin` can read any bank;
- non-admin staff cannot read the flag management API directly;
- toggle changes create audit log entries.

- [ ] **Step 5: Add backend guards**

Every new module router must call `require_feature_enabled` before returning business data or mutating state:

| Router | Feature key |
| --- | --- |
| `/api/employee-directory` | `employee_directory` |
| `/api/market-utilities` | `market_time` |
| `/api/staff-work-items` | `staff_inbox` |
| `/api/notifications` | `notifications` |
| `/api/ceo-messages` | `ceo_messages` |
| `/api/knowledge-gaps` | `knowledge_gaps` |
| `/api/policy-changes` | `policy_changes` |
| `/api/audit-evidence` | `audit_evidence_pack` |
| `/api/complaint-workspace` | `complaint_workspace` |
| `/api/branch-responses` | `branch_response_builder` |
| `/api/kyc-case-prep` | `kyc_case_prep` |
| `/api/checklist-workspace` | `checklist_validator` |

- [ ] **Step 6: Add frontend feature context**

`FeatureFlagContext` should:

- fetch effective feature flags after login;
- expose `isFeatureEnabled(featureKey)`;
- hide disabled navigation items;
- hide disabled dashboard widgets;
- show a neutral "Feature not enabled for this bank" page if a user opens a disabled route directly;
- refresh when Super Admin toggles a feature.

- [ ] **Step 7: Add Super Admin UI**

Create `/admin/features` with:

- bank selector for super admin;
- feature list grouped by Daily Work, Communications, Utilities, Banking Workflows, Knowledge, Governance;
- toggle per feature;
- reason field for disabling/enabling;
- last configured by/date;
- warning that disabling a feature hides it and blocks its API but does not delete existing data.

- [ ] **Step 8: Add tests**

Verify:

- new feature defaults disabled;
- Super Admin can enable/disable a bank feature;
- bank admin cannot toggle;
- staff cannot read/toggle flags through management API;
- disabled feature API returns `403` with `feature_disabled`;
- enabled feature API proceeds to its normal authorization checks;
- flag changes write audit events.

---

## Task 1: Employee Profile Schema

**Files:**
- Create: `backend/app/models/employee_profile.py`
- Create: `backend/alembic/versions/015_employee_profiles.py`
- Modify: `backend/app/models/user.py`
- Test: `backend/tests/test_employee_directory.py`

- [ ] **Step 1: Add failing schema test**

```python
def test_employee_profile_is_bank_scoped_and_linked_to_user():
    with Session(engine) as session:
        bank = Bank(name="Directory Bank", code="DIR01")
        session.add(bank)
        session.commit()
        session.refresh(bank)
        user = User(
            email="ram.ops@test.local",
            password_hash=get_password_hash("Password1"),
            name="Ram Ops",
            role="staff_user",
            department="Operations",
            bank_id=bank.id,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        profile = EmployeeProfile(
            bank_id=bank.id,
            user_id=user.id,
            branch="Kathmandu Main",
            job_title="Branch Operations Officer",
            extension="221",
            expertise_tags_json='["KYC", "cash operations"]',
            escalation_areas_json='["branch operations"]',
            availability_status="available",
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

        assert profile.user_id == user.id
        assert profile.bank_id == bank.id
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_employee_directory.py::test_employee_profile_is_bank_scoped_and_linked_to_user -q
```

Expected: fails because `EmployeeProfile` does not exist.

- [ ] **Step 3: Implement model**

Create `backend/app/models/employee_profile.py`:

```python
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class EmployeeProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id", index=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    branch: Optional[str] = Field(default=None, index=True)
    job_title: Optional[str] = Field(default=None, index=True)
    phone_extension: Optional[str] = None
    supervisor_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    expertise_tags_json: str = Field(default="[]")
    escalation_areas_json: str = Field(default="[]")
    availability_status: str = Field(default="available")
    public_notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 4: Add Alembic migration**

Create `backend/alembic/versions/015_employee_profiles.py` with columns matching the model, plus indexes on `bank_id`, `user_id`, `branch`, and `job_title`.

- [ ] **Step 5: Run test again**

Expected: PASS.

---

## Task 2: Employee Directory Search API

**Files:**
- Create: `backend/app/schemas/employee_directory.py`
- Create: `backend/app/services/employee_directory_service.py`
- Create: `backend/app/api/employee_directory.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_employee_directory.py`

- [ ] **Step 1: Add failing API tests**

Add tests for:

- staff can search active users in their own bank;
- staff cannot see another bank's users;
- staff cannot see disabled users;
- bank admin can include disabled users with `include_disabled=true`;
- search matches name, email, department, branch, job title, expertise tags, and escalation areas.

- [ ] **Step 2: Implement response schema**

`EmployeeDirectoryResult` should expose:

```python
id: int
name: str
email: str
role: str
department: str | None
branch: str | None
job_title: str | None
phone_extension: str | None
supervisor_user_id: int | None
expertise_tags: list[str]
escalation_areas: list[str]
availability_status: str
is_active: bool
can_message: bool
```

- [ ] **Step 3: Implement service search**

Search should:

- require `current_user.bank_id`;
- filter `User.bank_id == current_user.bank_id`;
- filter `User.is_active == True` unless admin requests disabled users;
- use case-insensitive matching over safe profile/user fields;
- limit results to 50 by default and 100 max;
- not return password hashes or private HR fields.

- [ ] **Step 4: Implement router**

Endpoint:

```text
GET /api/employee-directory?q=&department=&role=&branch=&expertise=&include_disabled=false&limit=50
```

Use `get_current_user`. Super admins can pass `bank_id`; other roles cannot.

- [ ] **Step 5: Register router**

Add to `backend/app/main.py`:

```python
app.include_router(employee_directory.router, prefix=f"{settings.API_V1_STR}/employee-directory", tags=["employee-directory"])
```

- [ ] **Step 6: Run tests**

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_employee_directory.py -q
```

---

## Task 3: Employee Directory UI

**Files:**
- Create: `frontend/src/pages/EmployeeDirectory.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/config/rolePermissions.js`
- Optional modify: `frontend/src/components/messenger/SecureMessengerWidget.jsx`

- [ ] **Step 1: Add permission**

Add `VIEW_EMPLOYEE_DIRECTORY: 'view_employee_directory'` to `PERMISSIONS`.

Grant it to:

- `staff_user`
- `compliance_user`
- `compliance_officer`
- `document_reviewer`
- `auditor`
- `data_auditor`
- `bank_admin`
- `super_admin`

- [ ] **Step 2: Add route**

In `frontend/src/App.jsx` import `EmployeeDirectory` and add:

```jsx
<Route path="employees" element={<EmployeeDirectory />} />
```

- [ ] **Step 3: Add sidebar item**

Add to the main or governance section:

```js
{ icon: 'badge', label: 'Employee Directory', to: '/employees', permission: PERMISSIONS.VIEW_EMPLOYEE_DIRECTORY }
```

- [ ] **Step 4: Build page behavior**

The page should include:

- search input;
- department, role, branch, and expertise filters;
- result cards/table;
- message action that calls `/messenger/conversations/direct`;
- empty state;
- loading state;
- admin-only include-disabled toggle.

- [ ] **Step 5: Verify frontend**

```bash
cd frontend
npm run lint
npm run build
```

---

## Task 4: Staff Daily Inbox Data Model

**Files:**
- Create: `backend/app/models/staff_work_item.py`
- Create: `backend/alembic/versions/016_staff_work_items.py`
- Create: `backend/app/schemas/staff_work_item.py`
- Create: `backend/app/services/staff_work_item_service.py`
- Create: `backend/app/api/staff_work_items.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_staff_work_items.py`

- [ ] **Step 1: Define shared work item**

Fields:

- `id`
- `bank_id`
- `assigned_to_user_id`
- `created_by_user_id`
- `source_type`
- `source_id`
- `title`
- `description`
- `priority`: `low`, `normal`, `high`, `urgent`
- `status`: `open`, `in_progress`, `waiting_review`, `completed`, `dismissed`
- `due_at`
- `completed_at`
- `metadata_json`
- `created_at`
- `updated_at`

- [ ] **Step 2: Add access tests**

Rules:

- staff can list their assigned items;
- bank admins can list bank-wide items;
- users cannot read another bank's items;
- completed/dismissed filters work.

- [ ] **Step 3: Implement API**

Endpoints:

```text
GET /api/staff-work-items
POST /api/staff-work-items
PATCH /api/staff-work-items/{item_id}
```

- [ ] **Step 4: Create frontend inbox page**

Create `frontend/src/pages/StaffInbox.jsx` and route `/inbox`.

Cards should group:

- due today;
- assigned document reviews;
- policy acknowledgement items;
- unread CEO messages requiring acknowledgement;
- unread notifications and urgent alerts;
- complaint drafts;
- long-document jobs;
- knowledge gaps needing owner review.

---

## Task 5: Notifications And Alerts

**Files:**
- Create: `backend/app/models/notification.py`
- Create: `backend/alembic/versions/017_notifications.py`
- Create: `backend/app/schemas/notification.py`
- Create: `backend/app/services/notification_service.py`
- Create: `backend/app/api/notifications.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/pages/Notifications.jsx`
- Create: `frontend/src/components/notifications/NotificationBell.jsx`
- Test: `backend/tests/test_notifications.py`

- [ ] **Step 1: Add notification model**

Fields:

- `id`
- `bank_id`
- `recipient_user_id`
- `created_by_user_id`
- `title`
- `body`
- `category`: `system`, `policy`, `work_item`, `ceo_message`, `document`, `model`, `security`, `compliance`
- `severity`: `info`, `warning`, `urgent`, `critical`
- `source_type`
- `source_id`
- `action_url`
- `read_at`
- `acknowledged_at`
- `expires_at`
- `metadata_json`
- `created_at`

- [ ] **Step 2: Add alert preference model**

Add `NotificationPreference` with:

- `bank_id`
- `user_id`
- `category`
- `in_app_enabled`
- `email_enabled` default false for now
- `urgent_only` default false

Do not implement email sending in this release. Store preferences only.

- [ ] **Step 3: Add access tests**

Verify:

- users can list only their own notifications;
- users cannot read another bank's notifications;
- users can mark their own notifications read/acknowledged;
- bank admins can create bank-scoped notifications;
- staff cannot create critical/security alerts.

- [ ] **Step 4: Implement API**

Endpoints:

```text
GET /api/notifications?status=unread&category=&severity=&limit=50
GET /api/notifications/unread-count
POST /api/notifications
PATCH /api/notifications/{notification_id}/read
PATCH /api/notifications/{notification_id}/acknowledge
GET /api/notifications/preferences
PATCH /api/notifications/preferences
```

- [ ] **Step 5: Integrate producers**

Create notifications when:

- long-document analysis job completes or fails;
- a work item is assigned;
- a policy change is published;
- a CEO message is published to the user;
- a document is approved, disabled, or needs review;
- bank readiness has blockers or urgent warnings.

- [ ] **Step 6: Frontend**

Add:

- top-bar notification bell with unread count;
- `/notifications` page;
- severity badges;
- category filters;
- read/acknowledge actions;
- link to source workflow using `action_url`.

---

## Task 6: CEO Message Center

**Files:**
- Create: `backend/app/models/ceo_message.py`
- Create: `backend/alembic/versions/018_ceo_messages.py`
- Create: `backend/app/schemas/ceo_message.py`
- Create: `backend/app/services/ceo_message_service.py`
- Create: `backend/app/api/ceo_messages.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/pages/CeoMessages.jsx`
- Test: `backend/tests/test_ceo_messages.py`

- [ ] **Step 1: Add CEO message model**

`CeoMessage` fields:

- `id`
- `bank_id`
- `created_by_user_id`
- `title`
- `body`
- `summary`
- `priority`: `normal`, `important`, `urgent`
- `audience_type`: `all_staff`, `department`, `branch`, `role`, `selected_users`
- `audience_json`
- `requires_acknowledgement`
- `published_at`
- `expires_at`
- `status`: `draft`, `published`, `archived`
- `created_at`
- `updated_at`

`CeoMessageAcknowledgement` fields:

- `id`
- `bank_id`
- `message_id`
- `user_id`
- `read_at`
- `acknowledged_at`
- `created_at`

- [ ] **Step 2: Add authorization rules**

Rules:

- `bank_admin` and `super_admin` can create and publish by default.
- Add a future-safe role/permission `MANAGE_CEO_MESSAGES`.
- Staff can list published messages addressed to them.
- Staff cannot see draft messages.
- Users cannot see messages from another bank.

- [ ] **Step 3: Publish behavior**

When a CEO message is published:

- resolve recipients by audience;
- create acknowledgement rows for recipients;
- create notifications for recipients;
- create Staff Work Items when `requires_acknowledgement=True`;
- audit the publish event.

- [ ] **Step 4: API**

Endpoints:

```text
GET /api/ceo-messages
POST /api/ceo-messages
GET /api/ceo-messages/{message_id}
PATCH /api/ceo-messages/{message_id}
POST /api/ceo-messages/{message_id}/publish
PATCH /api/ceo-messages/{message_id}/archive
PATCH /api/ceo-messages/{message_id}/acknowledge
GET /api/ceo-messages/{message_id}/acknowledgements
```

- [ ] **Step 5: UI**

Create `/ceo-messages` with:

- message list for staff;
- unread/acknowledgement-required filters;
- message detail view;
- acknowledge button;
- admin composer;
- audience selector for all staff, departments, branches, roles, and selected users;
- acknowledgement progress table for admins.

- [ ] **Step 6: Tests**

Verify:

- published all-staff message reaches active same-bank users;
- department audience reaches only matching department;
- branch audience uses employee profile branch;
- draft is hidden from staff;
- acknowledgement writes timestamp;
- publication creates notifications and work items when required.

---

## Task 7: Market And Time Utilities

**Files:**
- Create: `backend/app/models/market_utility.py`
- Create: `backend/alembic/versions/019_market_utilities.py`
- Create: `backend/app/schemas/market_utility.py`
- Create: `backend/app/services/market_utility_service.py`
- Create: `backend/app/api/market_utilities.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/pages/MarketAndTime.jsx`
- Create: `frontend/src/components/market/ExchangeRatePanel.jsx`
- Create: `frontend/src/components/market/BankingDatePanel.jsx`
- Create: `frontend/src/components/market/WorldClockPanel.jsx`
- Test: `backend/tests/test_market_utilities.py`

- [ ] **Step 1: Add exchange-rate batch model**

`ExchangeRateBatch` fields:

- `id`
- `bank_id`
- `batch_label`: `morning`, `midday`, `afternoon`, `special`, or bank-defined label
- `source_name`: `Treasury Desk`, `Core Banking Upload`, `NRB Reference`, etc.
- `source_url`
- `rate_date`
- `effective_from`
- `effective_to`
- `status`: `draft`, `published`, `superseded`, `archived`
- `published_by_user_id`
- `approved_by_user_id`
- `published_at`
- `notes`
- `metadata_json`
- `created_at`
- `updated_at`

The bank normally publishes rates 2-3 times per day. The UI must show the currently effective published batch, not a pretend live market feed.

- [ ] **Step 2: Add exchange-rate row model**

`ExchangeRateSnapshot` fields:

- `id`
- `bank_id`
- `batch_id`
- `source_name`
- `source_url`
- `rate_date`
- `base_currency`: default `NPR`
- `currency_code`: `USD`, `EUR`, `INR`, etc.
- `currency_name`
- `unit`
- `buy_rate`
- `sell_rate`
- `middle_rate`
- `source_published_at`
- `fetched_at`
- `is_manual_override`
- `stale_after_minutes`
- `metadata_json`

Store rates as decimals, not floats. Always show batch label, source, effective time, published time, and stale/superseded state in the UI.

- [ ] **Step 3: Add banking calendar model**

`BankingCalendarEvent` fields:

- `id`
- `bank_id`
- `title`
- `event_type`: `holiday`, `cutoff`, `settlement`, `maintenance`, `branch_notice`
- `starts_at`
- `ends_at`
- `timezone`
- `branch`
- `department`
- `applies_to_all_branches`
- `metadata_json`
- `created_at`

- [ ] **Step 4: Add service rules**

The service should:

- return the latest currently effective published bank-scoped exchange-rate batch;
- keep draft batches hidden from normal staff;
- mark rates stale when no published batch exists within the bank-configured freshness window;
- default freshness warning to 8 hours unless configured differently by the bank;
- allow manual Treasury/admin entry, CSV paste/upload, or future core-banking feed ingestion;
- supersede the previous active batch when a new batch is published;
- create a notification when a new published batch is available;
- never present exchange rates as trading advice;
- expose current bank local time using configured timezone, defaulting to `Asia/Kathmandu`;
- expose useful world clocks for configured treasury/correspondent zones;
- convert Gregorian date display and Nepali/B.S. display only if a tested conversion library or explicit bank calendar source is available;
- otherwise show Gregorian date and a clear `nepali_date_available=false` flag.

- [ ] **Step 5: Add API**

Endpoints:

```text
GET /api/market-utilities/exchange-rates?date=&currency=
GET /api/market-utilities/exchange-rate-batches
POST /api/market-utilities/exchange-rate-batches
PATCH /api/market-utilities/exchange-rate-batches/{batch_id}
POST /api/market-utilities/exchange-rate-batches/{batch_id}/publish
POST /api/market-utilities/exchange-rate-batches/{batch_id}/archive
GET /api/market-utilities/time
GET /api/market-utilities/world-clock
GET /api/market-utilities/calendar?from=&to=&branch=&department=
POST /api/market-utilities/calendar
```

Access:

- all active bank users can read;
- only bank admins/super admins or future `MANAGE_MARKET_UTILITIES` users can create, edit, publish, or archive rate batches and calendar events;
- no user can read another bank's market/calendar rows.

- [ ] **Step 6: Add tests**

Verify:

- same-bank users can read latest rates;
- other-bank rates do not leak;
- draft rate batches are hidden from staff;
- latest published effective batch is returned;
- stale rates return `is_stale=true` when the last published batch is older than the freshness window;
- publishing a new batch supersedes the previous active batch;
- rate batch publishing is admin/treasury-only;
- publishing rates creates notifications for configured recipients;
- calendar events are bank-scoped;
- time endpoint returns configured bank timezone;
- Nepali date conversion is disabled with an explicit flag if no converter is installed.

- [ ] **Step 7: Frontend page**

Create `/market-time` with:

- exchange-rate table for the current published batch;
- batch label, source, effective window, published time, and stale warning;
- buy/sell/middle rate columns;
- currency filter;
- previous batch/history drawer;
- bank local clock;
- world clocks for configured zones;
- today's date and banking calendar events;
- upcoming holidays/cutoffs/maintenance notices;
- admin-only rate batch editor with paste/CSV entry and calendar event entry.

- [ ] **Step 8: Add dashboard widgets**

Add compact widgets to Dashboard or Staff Inbox:

- today's bank local time;
- latest USD/INR/EUR rates or bank-configured priority currencies;
- stale-rate warning;
- latest batch label and effective time;
- next cutoff/holiday.

---

## Task 8: Knowledge Gap Dashboard

**Files:**
- Create: `backend/app/models/knowledge_gap.py`
- Create: `backend/alembic/versions/020_knowledge_gaps.py`
- Create: `backend/app/services/knowledge_gap_service.py`
- Create: `backend/app/api/knowledge_gaps.py`
- Modify: `backend/app/api/chat.py`
- Create: `frontend/src/pages/KnowledgeGaps.jsx`
- Test: `backend/tests/test_knowledge_gaps.py`

- [ ] **Step 1: Add gap model**

Track:

- bank;
- session;
- user;
- original question;
- rewritten retrieval query;
- mode;
- gap type: `not_found`, `low_source_confidence`, `unsupported_policy`, `stale_source`;
- status: `open`, `assigned`, `document_uploaded`, `resolved`, `dismissed`;
- owner;
- linked document;
- metadata.

- [ ] **Step 2: Capture not-found events**

When chat returns `NOT_FOUND_RESPONSE` in source-required modes, create or increment a knowledge gap.

- [ ] **Step 3: Add dashboard**

Admin/auditor view:

- top repeated unanswered questions;
- affected departments;
- linked document gaps;
- owner/status filters;
- button to create Staff Work Item.

- [ ] **Step 4: Tests**

Verify:

- not-found chat creates a gap;
- duplicate similar question increments count;
- staff cannot see another bank's gaps;
- admins can assign a gap to an employee.

---

## Task 9: Policy Change Digest And Acknowledgement

**Files:**
- Create: `backend/app/models/policy_change.py`
- Create: `backend/alembic/versions/021_policy_changes.py`
- Create: `backend/app/services/policy_change_service.py`
- Create: `backend/app/api/policy_changes.py`
- Create: `frontend/src/pages/PolicyChangeCenter.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Test: `backend/tests/test_policy_changes.py`

- [ ] **Step 1: Add policy change models**

Models:

- `PolicyChangeDigest`
- `PolicyChangeImpact`
- `PolicyAcknowledgement`

Digest fields:

- bank;
- new document;
- previous document;
- generated summary;
- affected departments;
- action items;
- source snippets;
- status: `draft`, `under_review`, `approved`, `published`;
- reviewer;
- timestamps.

- [ ] **Step 2: Generate digest**

Service compares:

- new document chunks;
- previous version chunks if linked;
- title/type/department/effective dates;
- retrieved excerpts through existing document chunks.

Use the LLM only to draft a staff-reviewable digest. Store disclaimer: not a regulatory guarantee.

- [ ] **Step 3: Acknowledgement flow**

When a digest is published, create acknowledgement rows or Staff Work Items for affected departments/users.
Also create notifications for impacted owners and departments.

- [ ] **Step 4: UI**

Page sections:

- pending digest reviews;
- published policy changes;
- acknowledgement progress;
- affected departments;
- source evidence panel.

---

## Task 10: Audit Evidence Pack

**Files:**
- Create: `backend/app/services/audit_evidence_service.py`
- Create: `backend/app/api/audit_evidence.py`
- Modify: `backend/app/main.py`
- Create: `frontend/src/components/trust/AuditEvidenceExportButton.jsx`
- Test: `backend/tests/test_audit_evidence.py`

- [ ] **Step 1: Add API**

Endpoints:

```text
GET /api/audit-evidence/chat/{message_id}
GET /api/audit-evidence/long-document-analysis/{job_id}
GET /api/audit-evidence/policy-change/{digest_id}
```

- [ ] **Step 2: Evidence payload**

Include:

- bank;
- user;
- timestamp;
- prompt/question;
- answer/result;
- model route/profile when available;
- sources;
- citation verification;
- source risk flags;
- staff review status;
- audit log IDs.

- [ ] **Step 3: Export format**

Start with JSON and printable browser view. Defer PDF export unless requested.

---

## Task 11: Complaint And Dispute Workspace Upgrade

**Files:**
- Prefer modify: `backend/app/models/support_case.py`
- Prefer modify: `backend/app/services/support_case_service.py`
- Prefer modify: `backend/app/api/support_cases.py`
- Create/modify: `frontend/src/pages/ComplaintWorkspace.jsx`
- Test: `backend/tests/test_complaint_workspace.py`

- [ ] **Step 1: Extend support cases instead of duplicating**

Add fields if missing:

- complaint category;
- channel;
- SLA due date;
- owner;
- escalation owner;
- required evidence checklist;
- customer-safe draft;
- internal note draft;
- source evidence;
- staff review status.

- [ ] **Step 2: Response builder**

Use approved source documents only for customer-facing policy claims. Every draft must include:

- source document;
- source passage;
- staff review required;
- what not to promise;
- escalation path if missing evidence.

- [ ] **Step 3: UI**

Add complaint queue, draft review, evidence checklist, and owner assignment.

---

## Task 12: Circular Impact Analyzer

**Files:**
- Prefer reuse: `backend/app/models/compliance_review.py`
- Prefer reuse: `backend/app/services/compliance_review_service.py`
- Prefer reuse: `backend/app/api/compliance_reviews.py`
- Modify: `frontend/src/pages/ComplianceWorkspace.jsx`
- Test: `backend/tests/test_circular_impact_analyzer.py`

- [ ] **Step 1: Extend compliance review**

Add:

- impacted product/process tags;
- affected document IDs;
- staff action items;
- owner assignments;
- due dates;
- acknowledgement requirement.

- [ ] **Step 2: Analyzer flow**

Input: circular document ID plus optional impacted departments.

Output:

- what changed;
- affected departments;
- impacted SOPs/products/forms;
- actions;
- due dates where source provides them;
- source citations;
- review disclaimer.

- [ ] **Step 3: Staff Work Item integration**

Approved impact items create work items for owners.

---

## Task 13: Branch Response Builder

**Files:**
- Create: `backend/app/services/branch_response_service.py`
- Create: `backend/app/api/branch_responses.py`
- Create: `frontend/src/pages/BranchResponseBuilder.jsx`
- Test: `backend/tests/test_branch_response_builder.py`

- [ ] **Step 1: Define request**

Fields:

- customer issue;
- channel;
- desired tone;
- selected document IDs optional;
- language.

- [ ] **Step 2: Generate source-backed draft**

Rules:

- source-required mode;
- refuse unsupported policy claims;
- include what staff can say;
- include what staff must not promise;
- include escalation owner/search hint from Employee Directory where possible.

- [ ] **Step 3: UI**

Show draft, source evidence, missing policy warning, and copy/export action.

---

## Task 14: KYC/AML Case Prep Assistant

**Files:**
- Create: `backend/app/models/kyc_case_prep.py`
- Create: `backend/alembic/versions/022_kyc_case_prep.py`
- Create: `backend/app/services/kyc_case_prep_service.py`
- Create: `backend/app/api/kyc_case_prep.py`
- Create: `frontend/src/pages/KycCasePrep.jsx`
- Test: `backend/tests/test_kyc_case_prep.py`

- [ ] **Step 1: Case prep model**

Track:

- customer/reference label;
- requested checklist type;
- provided documents;
- missing documents;
- red-flag notes;
- source evidence;
- escalation owner;
- human review required.

- [ ] **Step 2: No autonomous AML decision**

Tests must assert:

- no field stores an automated approve/reject decision;
- all outputs are marked `human_review_required=True`;
- source gaps produce a not-found or escalation note.

---

## Task 15: Document Checklist Validator

**Files:**
- Create: `backend/app/models/checklist_workspace.py`
- Create: `backend/alembic/versions/023_checklist_workspace.py`
- Create: `backend/app/services/checklist_workspace_service.py`
- Create: `backend/app/api/checklist_workspace.py`
- Create: `frontend/src/pages/ChecklistValidator.jsx`
- Test: `backend/tests/test_checklist_workspace.py`

- [ ] **Step 1: Checklist templates**

Fields:

- bank;
- workflow type: loan, onboarding, account maintenance, remittance, trade finance;
- required items JSON;
- optional items JSON;
- source document IDs;
- status.

- [ ] **Step 2: Validation result**

For an uploaded file pack or selected session documents:

- detected items;
- missing items;
- unclear items;
- source/evidence;
- confidence;
- staff review required.

- [ ] **Step 3: UI**

Show checklist rows with `present`, `missing`, `unclear`, and evidence passages.

---

## Task 16: Navigation And Permissions Cleanup

**Files:**
- Modify: `frontend/src/config/rolePermissions.js`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `docs/architecture.md`
- Modify: `docs/security.md`

- [ ] **Step 1: Add permissions**

Add:

- `MANAGE_BANK_FEATURES`
- `VIEW_EMPLOYEE_DIRECTORY`
- `VIEW_STAFF_INBOX`
- `VIEW_NOTIFICATIONS`
- `MANAGE_ALERTS`
- `VIEW_CEO_MESSAGES`
- `MANAGE_CEO_MESSAGES`
- `VIEW_MARKET_UTILITIES`
- `MANAGE_MARKET_UTILITIES`
- `VIEW_KNOWLEDGE_GAPS`
- `MANAGE_POLICY_CHANGES`
- `USE_COMPLAINT_WORKSPACE`
- `USE_BRANCH_RESPONSE_BUILDER`
- `USE_KYC_CASE_PREP`
- `USE_CHECKLIST_VALIDATOR`

- [ ] **Step 2: Role defaults**

Staff:

- directory, inbox, notifications, CEO messages, market/time utilities, branch response, checklist validator.

Compliance:

- directory, inbox, notifications, CEO messages, market/time utilities, policy change, circular impact, knowledge gaps, complaint workspace, KYC prep.

Auditors:

- directory, inbox read-only, notifications, CEO messages, market/time utilities, knowledge gaps, policy changes, audit evidence.

Bank admins:

- all enabled bank-scoped modules including CEO messages, alert publishing, and market utility management, but not Super Admin feature toggles.

Super admins:

- all modules plus bank-level feature toggle management.

- [ ] **Step 3: Sidebar grouping**

Proposed sections:

- Daily Work: Inbox, Chat, Employee Directory, Staff Messenger.
- Communications: CEO Messages, Notifications.
- Utilities: Market And Time.
- Banking Workflows: Branch Response, Complaint Workspace, KYC Prep, Checklist Validator.
- Knowledge: Documents, Policy Changes, Compliance Workspace, Knowledge Gaps.
- Insights/Governance: Analytics, Evaluations, Model Lab, Reports, Audit, Users, Settings.

---

## Task 17: Documentation And Release Gate

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/security.md`
- Modify: `docs/deployment/bank-readiness-checklist.md`
- Create: `docs/internal-banking-workspace.md`

- [ ] **Step 1: Write user-facing workflow doc**

`docs/internal-banking-workspace.md` should explain:

- Super Admin feature controls;
- Employee Directory;
- Staff Inbox;
- CEO Message Center;
- Notifications and Alerts;
- Market And Time utilities;
- Policy Change Center;
- Knowledge Gap Dashboard;
- complaint/dispute workspace;
- circular impact analyzer;
- branch response builder;
- KYC/AML prep;
- checklist validator;
- non-claims and staff-review rules.

- [ ] **Step 2: Add readiness evidence**

Bank readiness checklist should include:

- Super Admin feature-toggle test;
- employee directory bank-isolation test;
- CEO message audience and acknowledgement test;
- notification ownership/read-state test;
- exchange-rate batch publish/stale-state/bank-isolation test;
- work item ownership test;
- not-found gap capture test;
- policy acknowledgement test;
- complaint draft human-review test;
- KYC no-automated-decision test.

- [ ] **Step 3: Final verification**

Run:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_feature_flags.py backend/tests/test_employee_directory.py backend/tests/test_staff_work_items.py backend/tests/test_notifications.py backend/tests/test_ceo_messages.py backend/tests/test_market_utilities.py backend/tests/test_knowledge_gaps.py backend/tests/test_policy_changes.py backend/tests/test_audit_evidence.py -q
cd frontend && npm run lint && npm run build
git diff --check
```

---

## Acceptance Criteria

- Employee search never leaks another bank's users.
- New modules default disabled until Super Admin enables them for a bank.
- Disabled modules are hidden from navigation and return backend `403 feature_disabled`.
- Feature toggle changes are audit logged with actor, bank, feature key, state, and reason.
- Disabled users are hidden from staff.
- Employee search integrates with Staff Messenger.
- Staff Inbox shows assigned daily work from multiple modules.
- Notifications are bank-scoped, recipient-scoped, and support unread/read/acknowledged states.
- Urgent alerts are permission-gated and auditable.
- CEO messages support draft, publish, archive, targeted audiences, notifications, and acknowledgements.
- Staff see only published CEO messages addressed to them.
- Market And Time shows bank-published exchange-rate batches with source, effective time, published time, and stale warnings.
- Exchange rates are bank-scoped and draft batches are hidden from staff.
- Rate publication is permission-gated and creates notifications where configured.
- Time/date utilities clearly label bank timezone and do not invent Nepali date conversion when no tested converter/source is installed.
- Not-found source-required chat creates a knowledge gap.
- Policy digests require review before publication.
- Acknowledgements are trackable by user/department.
- Complaint and branch response drafts include sources and staff-review warnings.
- KYC/AML prep never stores or returns automated approve/reject decisions.
- Checklist validation labels missing/unclear evidence instead of pretending certainty.
- All new workflow outputs include audit evidence.
- Backend tests, frontend lint, frontend build, and `git diff --check` pass.

## Execution Recommendation

Build in this order:

1. Super Admin Feature Controls.
2. Employee Directory + Expert Finder.
3. Market And Time Utilities.
4. Staff Inbox.
5. Notifications And Alerts.
6. CEO Message Center.
7. Knowledge Gaps.
8. Policy Change Digest.
9. Audit Evidence Pack.
10. Complaint/Dispute Workspace upgrade.
11. Circular Impact Analyzer.
12. Branch Response Builder.
13. KYC/AML Prep.
14. Checklist Validator.

This order makes the product useful quickly, then turns the daily workspace into a platform for the banking-specific workflows.
