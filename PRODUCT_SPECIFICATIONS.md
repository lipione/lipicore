# BankAi Product Specifications

**Product:** Airgapped white-label bank AI appliance
**Delivery:** Bank-controlled infrastructure plus enterprise software
**Version:** 1.4
**Last updated:** 2026-06-04

---

## Executive Summary

BankAi is a private GPT-style assistant for bank staff. It runs on bank-owned or bank-controlled infrastructure, uses local vLLM model servers, and answers from approved internal documents with source evidence, clause/page citation metadata, audit logging, and role-aware access controls.

The current product is strongest as an internal knowledge, document analysis, customer-care support, compliance research, drafting, and day-to-day employee workspace tool. It should not be sold as an autonomous decisioning system, a regulator-approved compliance engine, or a guaranteed substitute for human review.

## Core Capabilities

- Staff chat with streaming responses, conversation history, and selected-document context.
- Local vLLM model routes exposed to staff as LipiFast and LipiCore. OCR extraction uses open-source Tesseract plus direct document parsers by default. The current production server routes all text lanes through LipiCore and keeps the LipiFast lane disabled until GPU capacity is rebalanced.
- Retrieval-augmented generation over uploaded and approved documents.
- Hybrid retrieval using Qdrant vector search plus PostgreSQL full-text search.
- Reranking before context construction.
- Source passage viewer with document, document heading, clause number, PDF page, printed page when available, section metadata, snippet, passage, and relevance metadata.
- Policy citation fidelity for policy, procedure, circular, directive, SOP, law, act, and compliance answers; missing required heading, clause, or PDF page metadata returns a citation-incomplete review response.
- Citation verification metadata displayed in chat.
- Document lifecycle states: `draft`, `approved`, `superseded`, `archived`, and `disabled`.
- Chunk-level permission metadata copied into PostgreSQL and Qdrant.
- Redis/RQ ingestion queue with a separate worker process.
- Adaptive chunk profiles for default text, section-heavy policy/regulatory text, spreadsheets/tables, presentations, and OCR-heavy inputs.
- Open-source OCR fallback and table-aware extraction for PDFs and spreadsheets.
- Queued long-document analysis for heavy OCR, large PDFs, and detailed Excel/PDF review.
- Compliance Workspace for circular/review notes with human sign-off.
- OCR Extraction workspace for transient text extraction from supported documents and images without indexing.
- Model Lab for model inventory, route visibility, and benchmark evidence.
- RAG Evaluation Center for bank-specific test cases.
- Optional internal banking workspace modules controlled by Super Admin feature flags: Employee Search, Staff Inbox, Notifications & Alerts, CEO's Message, Forex/Time/Dates, Knowledge Gaps, Policy Changes, Audit Evidence Packs, Complaint Workspace, Circular Impact Analyzer, Branch Response Builder, KYC Case Prep, and Checklist Validator.
- Audit logs, RBAC, bank partitioning, and white-label branding.
- Health-gated upgrade script for remote deployments.

## Supported Staff Workflows

| Workflow | Current Fit | Notes |
|----------|-------------|-------|
| Customer-care policy lookup | Strong | Best first MVP workflow because answers can cite approved support docs. |
| Compliance circular search | Strong | Requires approved document governance and evaluation sets. |
| Internal policy Q&A | Strong | Works when policies are uploaded, approved, and kept current. |
| Drafting emails/replies | Good | Should be reviewed by staff before use. |
| OCR text extraction | Strong | Extracts text from supported files without adding them to approved knowledge. |
| Document summarization | Good | Best for normal PDFs, Word files, spreadsheets, and PowerPoints. |
| Large document analysis | Good but queue-based | Heavy OCR, large PDFs, and detailed Excel workbooks run as background jobs with stored results. |
| Multi-document comparison | Good but bounded | Long, broad answers need queued analysis, multi-step retrieval, or map-reduce improvements. |
| Compliance review notes | Controlled support | Can summarize circular impact and review notes. Officers remain responsible for interpretation and sign-off. |
| Employee search | Strong when enabled | Searches bank-scoped staff profiles by department, branch, role, expertise, and escalation area. |
| Notifications and CEO messages | Strong when enabled | Supports audience targeting, read state, acknowledgement, expiry, and audit records. |
| Forex/time/date utilities | Good when enabled | Shows local banking time, business date, UTC time, and bank-published exchange-rate batches; Treasury/admin ownership required. |
| Staff Inbox and workflow helpers | Controlled support | Supports staff-reviewable work items, cases, drafts, and checklists. Does not replace approval workflows. |
| Credit/risk decisioning | Not ready | Requires validated workflow controls, integrations, supervisor review, and a bank-approved governance model. |
| Regulatory reporting automation | Not ready | Needs structured workflows, source validation, and formal sign-off. |

## File Support

| Format | Status | Limitations |
|--------|--------|-------------|
| PDF | Supported | Scanned PDFs depend on OCR quality; charts, handwriting, seals, and signatures remain weak. |
| DOCX | Supported | Complex embedded objects may be flattened or ignored. |
| XLSX/XLS | Supported | Sheet names, merged ranges, and cell coordinates are preserved; spreadsheet formulas/models are not deeply interpreted. |
| PPTX | Supported | Text extraction works; visual layouts/charts are limited. |
| TXT/CSV | Supported | Good fit for policy, FAQ, and tabular text imports. |
| Images | Partial | Open-source OCR fallback exists, but should not be treated as high-accuracy for bank-critical evidence. |

## Queued Long-Document Analysis

Large PDFs, OCR-heavy documents, and detailed Excel workbooks should use queued long-document analysis instead of normal chat. The workflow creates a background job, extracts document content, selects relevant page/sheet excerpts within the analyst-model context budget, generates a staff-reviewable result, and stores progress/result metadata in PostgreSQL.

Current defaults:

- Document Library upload limit: 50 MB.
- OCR engine: open-source Tesseract with `OCR_LANGUAGES=eng+nep` by default.
- OCR fallback cap: `OCR_MAX_PAGES=200`.
- Degraded Nepali PDF text layers can fall back to OCR on affected pages.
- Optional Vision Review uses LipiCore after OCR for PDF/image review notes only, capped by `OCR_VISION_REVIEW_MAX_PAGES=3`.
- Job timeout: `INGESTION_JOB_TIMEOUT_SECONDS=1800`.
- Worker concurrency: `INGESTION_WORKER_CONCURRENCY=1`.
- Deep context budget: `LLM_DEEP_CONTEXT_WINDOW_TOKENS`, default 8192 tokens.

This is a controlled analysis workflow, not a guarantee of perfect OCR, perfect table interpretation, or autonomous compliance/lending decisions. See `docs/long-document-analysis.md`.

## RAG System

BankAi uses a defensive RAG pipeline rather than sending entire files to the model.

1. Files are uploaded and stored in MinIO.
2. Metadata is saved in PostgreSQL.
3. Redis/RQ queues ingestion work for extraction, OCR/table parsing, adaptive chunking, embedding, and indexing.
4. Chunks are stored with lifecycle, permission, source-risk, and policy citation metadata.
5. Retrieval combines Qdrant semantic search and PostgreSQL full-text search.
   Semantic search uses `BAAI/bge-m3` multilingual embeddings with 1024-dimensional vectors so English questions can retrieve relevant Nepali policy chunks more reliably than the previous English-centric MiniLM baseline.
6. Candidates are reranked, filtered by access rules and relevance threshold, then passed to the model.
7. Answers include source metadata, heading/clause/page citation metadata, and citation verification results.
8. Policy-like answers missing required heading, clause, or PDF page metadata return `citation_incomplete` instead of final policy advice.
9. Admins/auditors can run RAG evaluation cases against expected sources, expected headings/clauses/pages, and required citation terms.

This is stronger than a basic vector-only chatbot because it adds document governance, role filters, adaptive chunk profiles, reranking, citation evidence, policy citation completeness checks, queued long-document analysis, and measurable evaluation. It is still not perfect: citation verification is a lexical precheck plus configurable semantic matching (with optional NLI path when enabled), and broad multi-document synthesis still needs stronger map-reduce and evaluation coverage.

## Measured Test Baseline

These are test-server results, not contractual SLAs.

| Scenario | Result |
|----------|--------|
| Backend test suite | 37 tests passed on remote test server |
| Frontend build | `npm run build` passed |
| Frontend lint | `npm run lint` passed with zero errors and existing e2e console warnings only |
| Production deployment | `/data/bankai` deployed at commit `615d299`; migrations applied through `012` |
| Production route checks | Backend and frontend health checks passed; protected Model Lab and long-document endpoints return `401` unauthenticated |
| OCR extraction API | TXT extraction returns text without creating document records; unsupported files are rejected |
| Policy citation fidelity | Current local branch verifies extraction, ingestion, retrieval, citation backfill, evaluation, streaming persistence, and UI trust labels for heading/clause/page metadata |
| Internal workspace controls | Current local branch verifies feature flags, employee directory, market utilities, notifications, CEO messages, staff work items, and banking workflow services |
| 25 active staff token smoke | 442 requests, 0 failures, p95 stream around 17s |
| 50 active staff API smoke | 752 requests, 0 failures |
| 100 active staff API-only smoke | 2,357 requests, 0 failures, p95 around 57ms |
| 20 staff real streaming answers | 20/20 answers, p50 8.41s, p95 29.95s |
| 40 staff real streaming answers | 40/40 answers, p50 30.61s, p95 80.19s |

Interpretation: the system can support normal internal usage patterns, but analyst-model streaming latency rises sharply under heavier simultaneous load. Whole-bank rollout requires capacity planning, queue limits, and pilot measurements on the bank's actual hardware and documents.

## Recommended Deployment Tiers

| Tier | Intended Use | Indicative Configuration |
|------|--------------|--------------------------|
| Pilot | 20-50 staff, one department | Single host, 1-2 GPUs, conservative queue limits, daily backups. |
| Department | 50-200 staff, customer care/compliance | Dedicated text/analyst capacity, optional separate fast route, monitored Redis queue, scheduled RAG evaluations, stronger backup/restore testing. |
| Whole-bank | 200+ staff across departments | HA PostgreSQL, HA object storage, Qdrant persistence/replication plan, multiple backend workers, redundant inference capacity, observability, runbooks. |

Single-host Docker Compose is acceptable for pilots and controlled internal trials. It is not by itself a 99.95% HA architecture.

## Production Requirements

- TLS on every staff-facing route.
- Strong secrets in `.env`; no committed credentials.
- Bank-controlled identity lifecycle and role assignment.
- Approved document governance before staff-wide release.
- Regular RAG evaluations using the bank's real policies and expected answers.
- Policy citation checks for heading, clause, PDF page, printed page where available, and citation-incomplete behavior.
- Super Admin feature-control review before enabling optional internal workspaces.
- Named bank owners for employee directory data, notifications, CEO messages, Staff Inbox, and exchange-rate updates where enabled.
- Representative long-document tests using clean PDFs, scanned PDFs, Excel workbooks, and bilingual documents before making large-file claims.
- Backup and restore drills for PostgreSQL, MinIO, and Qdrant.
- Firewall isolation for PostgreSQL, Qdrant, Redis, MinIO, backend debug ports, and model debug ports.
- Operational runbooks for upgrade, rollback, model restart, queue saturation, and disk pressure.

## Commercial Positioning

The strongest first offer is not "AI for the whole bank." It is:

> A private bank knowledge assistant for staff that answers from approved internal documents, shows evidence, and keeps usage auditable.

The first buyer should be a department with high document-lookup volume, such as customer care, compliance, operations, or credit administration. A bank-wide deployment should follow only after measured department adoption and successful evaluation scores.

## Claims That Require More Evidence

Do not use these claims in sales material until independently validated for the customer environment:

- Guaranteed 99.95% uptime.
- Regulator-approved compliance automation.
- SOC2, PCI DSS, ISO 27001, or NRB certification.
- 500+ simultaneous LLM users.
- Fixed ROI percentages.
- Perfect hallucination prevention.
- Fully automatic policy correctness from citation metadata alone.
- Live market-rate feed unless an approved provider integration is separately implemented.
- Full understanding of scanned, handwritten, chart-heavy, signed, sealed, or image-heavy documents.
- Instant large-file analysis under unlimited concurrent OCR/PDF/XLS load.

## Current Product Decision

**Status:** Pilot-ready with disciplined validation.

BankAi is technically credible as an airgapped staff AI appliance, but it should still be expanded only after the pilot proves three things: staff save time, answers cite correct approved sources, and bank operators can maintain the system without heroic support.
