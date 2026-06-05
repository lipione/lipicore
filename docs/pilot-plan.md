# Pilot Plan

## Phase 1: Internal Testing
- **Goal:** Validate basic RAG capability and document ingestion.
- **Users:** Internal development team.
- **Actions:** Upload sample dummy banking policies, test query accuracy, verify heading/clause/PDF page citation metadata, queue at least one large PDF/Excel analysis job, and refine chunking/context packing.

## Phase 2: Limited Bank Admin Trial
- **Goal:** Validate UI/UX and RBAC logic.
- **Users:** 1-2 designated "Bank Admins".
- **Actions:** Provide access to the Dashboard. Have admins create dummy users, upload test documents, configure only the agreed feature flags, publish one exchange-rate batch if `market_time` is enabled, and verify that isolation holds.

## Phase 3: Staff Mock Scenarios
- **Goal:** Evaluate the AI's response quality and safety guardrails.
- **Users:** Select group of staff members acting as end-users.
- **Actions:** Run simulated loan or policy queries, queued long-document analysis, citation-incomplete policy checks, unsupported-source questions, and enabled internal workspace flows. Monitor the `AuditLog` and long-document job table to ensure actions are captured. Evaluate the LLM's adherence to "I don't know" rules.

## Phase 4: Production Go-Live
- **Goal:** Full deployment.
- **Actions:** Transition to production infrastructure, final security audit, clear all mock data, begin live document ingestion, and set queue limits for heavy OCR/PDF/XLS jobs.

## Long-Document Pilot Evidence

Before a bank demo or pilot exit decision, test:

- One clean policy PDF.
- One scanned PDF or image-heavy document.
- One Excel workbook with formulas or merged cells.
- One bilingual document if Nepali use is expected.

Record job duration, result usefulness, source/page/sheet references, extraction issues, and whether staff correction was required.

## Internal Workspace Pilot Evidence

If optional workspace features are enabled, test and record:

- Employee Search by department, branch, role, and expertise.
- One CEO message with acknowledgement where required.
- One notification with read and acknowledgement behavior.
- One exchange-rate batch with source name, notes, publish time, and bank owner.
- One Staff Inbox work item assignment and completion.
- Feature-disabled behavior for at least one module that remains off.
