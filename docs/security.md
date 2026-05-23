# Security Architecture

## Isolation
- **Logical Isolation:** All critical database tables contain a `bank_id`. Qdrant queries strictly enforce `bank_id` filters before retrieval.
- **Physical Isolation (Optional):** The Docker Compose stack can be deployed on a physically isolated server or VPC per bank.

## Authentication & Authorization
- Passwords hashed using bcrypt.
- Stateless JWT authentication.
- Strict Role-Based Access Control (RBAC):
  - `super_admin`: Global system management.
  - `bank_admin`: Bank-level management, document approval.
  - `staff_user`: Query-only, restricted document access.
  - `compliance_user`, `compliance_officer`, `document_reviewer`: Review-oriented access to approved bank workflows where enabled.

## RAG Security
- **Prompt Guardrails:** Source-backed modes instruct the LLM to use approved context and refuse unsupported policy answers.
- **Source Verification:** Answers expose retrieved source passages, chunk metadata, and citation-verification status where sources are used. Verification is evidence for staff review, not a guarantee of regulatory correctness.

## Long-Document Analysis Security
- Long-document jobs are bank-scoped in PostgreSQL with `bank_id`, `document_id`, and `requested_by`.
- Staff users can see only their own long-document analysis jobs.
- Bank admin, compliance, compliance officer, document reviewer, and super admin roles can view bank-wide long-document jobs.
- Disabled, archived, superseded, and failed documents are blocked from new analysis jobs.
- Staff can analyze approved global knowledge documents and their own ready/indexed/approved session uploads only.

## Auditing
- Every API action (upload, approval, query) creates an `AuditLog` entry in the PostgreSQL database.
- Long-document jobs store status, prompt, result, error, and metadata for review. High-risk extracted content still requires staff review before action.
