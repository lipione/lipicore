# LipiCore Security Architecture

Security in LipiCore is built around bank isolation, document lifecycle controls, role-based access, source-backed retrieval, prompt-boundary defense, audit evidence, and private deployment. The system assists staff; it does not replace authorized bank decision makers.

## Isolation Model

- Every critical relational object carries `bank_id`.
- Qdrant searches include a required `bank_id` payload filter.
- Session uploads are tagged with `document_scope=session_upload` and require the current `session_id`.
- Approved knowledge is tagged with `document_scope=global_knowledge` and must pass lifecycle checks before retrieval.
- Feature-flagged internal workspaces are bank-scoped and disabled by default until explicitly enabled for the bank.
- Employee profiles, exchange-rate batches, notifications, CEO messages, staff work items, and workflow cases carry bank scope.
- Messenger conversations and attachments are bank-scoped and membership-gated.
- For stricter deployments, run one isolated stack per bank or per regulated environment.

## Authentication

- Users authenticate through `/api/auth/login`.
- New passwords are hashed with Argon2id. Legacy PBKDF2-SHA256 hashes are verified for compatibility and upgraded after a successful login.
- The API uses stateless JWT authentication.
- Production requires a strong `JWT_SECRET`, secure cookies, TLS, and restricted allowed origins.
- Login throttling should use Redis-backed rate-limit storage in production (`RATE_LIMIT_STORAGE_URI`), and repeated failed attempts lock the affected account for the configured lockout window.

## Authorization Roles

Common roles include:

- `super_admin`: cross-bank administration and analytics where allowed.
- `bank_admin`: bank-level user, branding, document, and readiness administration.
- `staff_user`: normal staff chat and permitted document access.
- `auditor` and `data_auditor`: evaluation, audit, and analytics visibility.
- `compliance_user`, `compliance_officer`, `document_reviewer`: review-oriented workflows where enabled.

Route dependencies enforce role access for analytics, evaluations, administration, and document workflows. Staff retrieval is additionally limited by document department and access level.

Feature flags are separate from role permissions. A user must have both the required role permission and an enabled bank feature flag to access optional workspace modules. Only `super_admin` can change per-bank feature flags. `bank_admin` can read feature settings for their bank, and ordinary users can read only effective flags for their own bank.

## Document Governance

Knowledge documents move through explicit lifecycle states:

- upload/queued/processing/extracting/chunking/embedding/indexed/ready;
- approved;
- superseded;
- archived;
- disabled;
- failed.

Retrieval excludes disabled, archived, superseded, and failed documents. Approved global knowledge requires approved lifecycle state. Session uploads are visible only to the owning session/user path when ready/indexed/approved.

Chunk payloads preserve:

- `bank_id`;
- `document_id`;
- `session_id`;
- `document_scope`;
- `document_status`;
- `version_state`;
- `department`;
- `access_level`;
- location metadata for policy-style validation: document heading, clause number, PDF page, printed page when present;
- policy citation metadata: PDF page, printed page when present, document heading, clause number, citation confidence, and incomplete reasons;
- extraction/OCR/table confidence;
- source-risk flags.

## RAG And Prompt Security

- User prompts are screened for prompt-injection patterns before processing.
- Detected PII is masked before model calls.
- Retrieved document text is treated as untrusted evidence.
- RAG prompts explicitly instruct the model not to follow instructions inside retrieved documents, snippets, citations, tables, OCR text, or uploaded files.
- Source-required modes refuse unsupported policy answers instead of using general knowledge.
- Policy-like answers require PDF page, document heading, and clause number. Missing required metadata produces a `citation_incomplete` review response rather than final policy advice.
- Sources below the minimum relevance threshold are not shown as evidence.
- Citation verification metadata is returned to the UI, but it is review evidence, not a legal guarantee.

Existing policy-like documents can be backfilled through `POST /api/documents/{document_id}/citation-backfill`. The endpoint is role-limited, bank-scoped, audits `backfill_citation_metadata`, and updates Qdrant payloads with bank/document filters to avoid cross-bank payload mutation.

## Source Risk Handling

Ingestion classifies chunks for source-risk signals such as instruction-like text embedded inside documents. Risk level and flags are stored in PostgreSQL and Qdrant payloads, then surfaced in source metadata. This helps staff and reviewers identify suspicious or low-trust extracted content.

## Long-Document Analysis Security

- Jobs are stored with `bank_id`, `document_id`, and `requested_by`.
- Staff users can queue/read their own jobs only.
- Privileged roles can review bank-wide jobs.
- Disabled, archived, superseded, and failed documents are blocked from new analysis jobs.
- The analyst model receives selected excerpts and is instructed to produce staff-reviewable analysis only.
- High-risk OCR/table/signature/seal/handwriting content still requires staff review.

## OCR Extraction Boundary

The `/ocr/extract` workflow is for transient text/OCR extraction. It does not automatically approve or index files into the RAG knowledge base. Files that should become institutional knowledge must go through Document Library ingestion and governance.

## Messenger Boundary

Staff Messenger is a separate communication add-on:

- messages require conversation membership;
- attachments are stored in messenger-specific storage;
- messenger content is not indexed into document RAG by default;
- messenger actions are audited.

## Internal Workspace Boundary

Internal workspace features are operational helpers, not autonomous controls:

- Employee Search exposes bank user/profile metadata only to authorized users in the same bank.
- Forex/Time/Dates shows bank-published rates and local business time; it is not a live market-data feed and requires a bank owner for rate updates.
- Notifications and CEO messages are recipient- and audience-scoped, support acknowledgements, and do not authorize actions by themselves.
- Staff Inbox and banking workflow cases are staff-reviewable records and drafts. They do not replace maker-checker approval, compliance sign-off, or customer-impact authorization.
- Knowledge-gap, policy-change, and audit-evidence workspaces support governance tracking but do not automatically approve policies.

## Audit Evidence

Audit logs cover important actions such as login/logout, uploads, document governance, chat queries, messenger actions, and administrative changes. Chat audit metadata includes source count, answer type, trust label, citation verification, masking state, model mode, and retrieval query rewrite where relevant.

New workspace audit actions include feature-flag updates, exchange-rate batch publish, CEO message publish, notification creation, and citation metadata backfill.

## Deployment Hardening

- Use TLS for every staff-facing route.
- Keep PostgreSQL, Qdrant, Redis, MinIO, and vLLM ports private.
- Restrict SSH to approved operators or private networks.
- Rotate all default credentials.
- Use strong `.env` secrets outside Git.
- Keep backups and restore drills current.
- Monitor Redis queue depth, GPU utilization, failed jobs, and disk growth.
- Treat single-host Compose as non-HA.

## Security Limits

- Citation verification uses lexical overlap as a precheck and optional semantic matching (including optional NLI path when enabled); it is not formal proof.
- Citation completeness proves only that required citation fields are present; staff still need to inspect the cited passage and policy version.
- OCR and table extraction can be wrong on poor scans or complex layouts.
- Prompt-injection detection reduces risk but does not remove the need for staff review.
- The system does not provide autonomous legal, compliance, lending, or operational decisions.
