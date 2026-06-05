# Internal Banking Workspace

The internal banking workspace adds day-to-day employee tools around the source-backed AI assistant. These modules are bank-scoped, role-aware, audit-friendly, and disabled by default until a Super Admin enables them for a bank.

## Feature Control Model

Feature availability is controlled by `/api/feature-flags`.

| Feature Key | Workspace | Default | Notes |
| --- | --- | --- | --- |
| `employee_directory` | Employee Search | Off | Search bank users and employee profile metadata. |
| `market_time` | Forex, Time & Dates | Off | Shows local banking time, business date, and bank-published exchange rates. |
| `staff_inbox` | Daily Inbox and Staff Messenger gate | Off | Work-item handoff and internal staff workflow queue. |
| `notifications` | Notifications & Alerts | Off | Bank alerts, acknowledgement, read state, and unread counts. |
| `ceo_messages` | CEO's Message | Off | Executive announcements with optional acknowledgement and notification fanout. |
| `knowledge_gaps` | Knowledge Gap Queue | Off | Tracks unanswered or missing-policy questions for follow-up. |
| `policy_changes` | Policy Change Watch | Off | Tracks policy updates and can create staff work items when inbox is enabled. |
| `audit_evidence_pack` | Audit Evidence Packs | Off | Builds evidence bundles for review and export workflows. |
| `complaint_workspace` | Complaint Workspace | Off | Drafts and tracks complaint response work. |
| `circular_impact_analyzer` | Circular Impact Analyzer | Off | Records circular impact summaries and affected workflow notes. |
| `branch_response_builder` | Branch Response Builder | Off | Creates branch operations response drafts. |
| `kyc_case_prep` | KYC Case Prep | Off | Prepares KYC review packets and exception notes. |
| `checklist_validator` | Checklist Validator | Off | Checks supplied files or items against required checklists. |

Super Admin can update flags with:

```text
PATCH /api/feature-flags/{bank_id}/{feature_key}
```

Bank Admin and Super Admin can read configured flags with:

```text
GET /api/feature-flags?bank_id={bank_id}
```

Any authenticated user can read effective flags for their bank with:

```text
GET /api/feature-flags/effective
```

When a feature is disabled, the backend returns `403` with `{"code": "feature_disabled", "feature": "<feature_key>"}` and the frontend shows a feature-unavailable state.

## Employee Search

Frontend route: `/employees`

API:

```text
GET /api/employee-directory
```

Supported filters:

- `q`
- `department`
- `role`
- `branch`
- `expertise`
- `include_disabled`
- `limit`
- `bank_id` for Super Admin bank selection

The directory searches active users by default and combines user data with optional employee profile fields: branch, job title, extension, supervisor, expertise tags, escalation areas, availability, and public notes. Only admins can include disabled employees. Cross-bank search is blocked for non-Super Admin users.

If Staff Inbox/Messenger is also enabled, directory results expose whether the current user can message the employee.

## Forex, Time And Dates

Frontend route: `/market-time`

API:

```text
GET /api/market-utilities/summary
GET /api/market-utilities/rate-batches
POST /api/market-utilities/rate-batches
```

The summary returns:

- bank ID;
- `Asia/Kathmandu` local server time;
- UTC time;
- local business date;
- the latest exchange-rate batch;
- the operating note: bank-published rates may be updated 2-3 times per business day.

Rates are not scraped from a public market feed. They are bank-published operational rates, typically entered by Treasury or an authorized admin. `super_admin` and `bank_admin` can publish rate batches. Each publish action is audited as `exchange_rate_batch_publish`.

## Notifications And Alerts

Frontend route: `/notifications`

API:

```text
GET /api/notifications
GET /api/notifications/unread-count
POST /api/notifications
PATCH /api/notifications/{notification_id}/read
PATCH /api/notifications/{notification_id}/acknowledge
```

Notifications are bank-scoped and recipient-specific. Supported targeting includes bank-wide, role, department, and explicit recipients. Notifications may include category, severity, source reference, action URL, expiry, and required acknowledgement.

Only admin roles can create notifications. Users can read, mark read, and acknowledge only their own notifications. Notification creation is audited as `notification_create`.

## CEO's Message

Frontend route: `/ceo-messages`

API:

```text
GET /api/ceo-messages
POST /api/ceo-messages
PATCH /api/ceo-messages/{message_id}/acknowledge
```

CEO messages are bank-scoped announcements targeted to the whole bank, a role, or a department. Messages can expire, require acknowledgement, and optionally fan out notifications when the `notifications` feature is also enabled.

Only `super_admin` and `bank_admin` can publish CEO messages. Publication is audited as `ceo_message_publish`.

## Staff Inbox

Frontend route: `/inbox`

API:

```text
GET /api/staff-work-items
POST /api/staff-work-items
PATCH /api/staff-work-items/{item_id}
```

Staff Inbox stores assigned work items with source type, source ID, title, description, priority, status, due date, completion timestamp, and metadata JSON. Admins can create and reassign work items. Staff can update their own assigned items. Bank-wide listing is admin-only.

## Banking Workflow Workspaces

The banking workflow workspaces share a common bank-scoped case model:

| Frontend Route | API Prefix | Feature Key |
| --- | --- | --- |
| `/complaints` | `/api/complaint-workspace` | `complaint_workspace` |
| `/circular-impact` | `/api/circular-impact` | `circular_impact_analyzer` |
| `/branch-responses` | `/api/branch-responses` | `branch_response_builder` |
| `/kyc-case-prep` | `/api/kyc-case-prep` | `kyc_case_prep` |
| `/checklists` | `/api/checklist-workspace` | `checklist_validator` |
| `/audit-evidence` | `/api/audit-evidence` | `audit_evidence_pack` |

These modules create staff-reviewable cases and summaries. They do not replace maker-checker approval, compliance officer sign-off, or customer-impact authorization.

## Security And Governance

- Every internal workspace object carries bank scope.
- Super Admin may select a bank where supported; non-Super Admin users cannot cross bank boundaries.
- Feature flags are off by default and auditable when changed.
- Exchange rates, notifications, CEO messages, and feature-flag changes create audit records.
- Messenger and Staff Inbox are operational communication/workflow systems; their content is not indexed into document RAG by default.
- Market rates are bank-published operational values and must be checked against the bank's Treasury process before customer-facing use.

