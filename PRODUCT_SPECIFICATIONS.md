# BankAi Product Specifications

**Product:** Airgapped white-label bank AI appliance
**Delivery:** Bank-controlled infrastructure plus enterprise software
**Version:** 1.3
**Last updated:** 2026-05-23

---

## Executive Summary

BankAi is a private GPT-style assistant for bank staff. It runs on bank-owned or bank-controlled infrastructure, uses local vLLM model servers, and answers from approved internal documents with source evidence, citation metadata, audit logging, and role-aware access controls.

The current product is strongest as an internal knowledge, document analysis, customer-care support, compliance research, and drafting tool. It should not be sold as an autonomous decisioning system, a regulator-approved compliance engine, or a guaranteed substitute for human review.

## Core Capabilities

- Staff chat with streaming responses, conversation history, and selected-document context.
- Local vLLM model routes for text/analyst work and vision/OCR work. The current production server routes all text lanes to Gemma 4 26B 4-bit and keeps the fast 4B lane disabled until GPU capacity is rebalanced.
- Retrieval-augmented generation over uploaded and approved documents.
- Hybrid retrieval using Qdrant vector search plus PostgreSQL full-text search.
- Reranking before context construction.
- Source passage viewer with document, page, section/chunk, snippet, passage, and relevance metadata.
- Citation verification metadata displayed in chat.
- Document lifecycle states: `draft`, `approved`, `superseded`, `archived`, and `disabled`.
- Chunk-level permission metadata copied into PostgreSQL and Qdrant.
- Redis/RQ ingestion queue with a separate worker process.
- OCR fallback and table-aware extraction for PDFs and spreadsheets.
- Queued long-document analysis for heavy OCR, large PDFs, and detailed Excel/PDF review.
- Support Desk for customer-care and branch cases with source-backed draft assistance.
- Compliance Workspace for circular/review notes with human sign-off.
- Loan Support workspace for missing-document tracking, risk-factor notes, and credit memo drafts without automated approval.
- Document Review queue for low-confidence extraction pages.
- Model Lab for model inventory, route visibility, and benchmark evidence.
- RAG Evaluation Center for bank-specific test cases.
- Audit logs, RBAC, bank partitioning, and white-label branding.
- Health-gated upgrade script for remote deployments.

## Supported Staff Workflows

| Workflow | Current Fit | Notes |
|----------|-------------|-------|
| Customer-care policy lookup | Strong | Best first MVP workflow because answers can cite approved support docs. |
| Compliance circular search | Strong | Requires approved document governance and evaluation sets. |
| Internal policy Q&A | Strong | Works when policies are uploaded, approved, and kept current. |
| Drafting emails/replies | Good | Should be reviewed by staff before use. |
| Document summarization | Good | Best for normal PDFs, Word files, spreadsheets, and PowerPoints. |
| Large document analysis | Good but queue-based | Heavy OCR, large PDFs, and detailed Excel workbooks run as background jobs with stored results. |
| Multi-document comparison | Good but bounded | Long, broad answers need queued analysis, multi-step retrieval, or map-reduce improvements. |
| Loan support notes | Controlled support | Can track required/missing documents, risk-factor notes, and credit memo drafts. It does not approve or reject loans. |
| Compliance review notes | Controlled support | Can summarize circular impact and review notes. Officers remain responsible for interpretation and sign-off. |
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
| Images | Partial | OCR/vision fallback exists, but should not be treated as high-accuracy for bank-critical evidence. |

## Queued Long-Document Analysis

Large PDFs, OCR-heavy documents, and detailed Excel workbooks should use queued long-document analysis instead of normal chat. The workflow creates a background job, extracts document content, selects relevant page/sheet excerpts within the analyst-model context budget, generates a staff-reviewable result, and stores progress/result metadata in PostgreSQL.

Current defaults:

- Document Library upload limit: 50 MB.
- OCR fallback cap: `OCR_MAX_PAGES=200`.
- Job timeout: `INGESTION_JOB_TIMEOUT_SECONDS=1800`.
- Worker concurrency: `INGESTION_WORKER_CONCURRENCY=1`.
- Deep context budget: `LLM_DEEP_CONTEXT_WINDOW_TOKENS`, default 8192 tokens.

This is a controlled analysis workflow, not a guarantee of perfect OCR, perfect table interpretation, or autonomous compliance/lending decisions. See `docs/long-document-analysis.md`.

## RAG System

BankAi uses a defensive RAG pipeline rather than sending entire files to the model.

1. Files are uploaded and stored in MinIO.
2. Metadata is saved in PostgreSQL.
3. Redis/RQ queues ingestion work for extraction, OCR/table parsing, chunking, embedding, and indexing.
4. Chunks are stored with lifecycle and permission metadata.
5. Retrieval combines Qdrant semantic search and PostgreSQL full-text search.
6. Candidates are reranked, filtered by access rules and relevance threshold, then passed to the model.
7. Answers include source metadata and citation verification results.
8. Admins/auditors can run RAG evaluation cases against expected sources and required citation terms.

This is stronger than a basic vector-only chatbot because it adds document governance, role filters, reranking, citation evidence, queued long-document analysis, and measurable evaluation. It is still not perfect: citation verification is lexical overlap, not formal entailment, and broad multi-document synthesis still needs stronger map-reduce and evaluation coverage.

## Measured Test Baseline

These are test-server results, not contractual SLAs.

| Scenario | Result |
|----------|--------|
| Backend test suite | 37 tests passed on remote test server |
| Frontend build | `npm run build` passed |
| Frontend lint | `npm run lint` passed with zero errors and existing e2e console warnings only |
| Production deployment | `/data/bankai` deployed at commit `615d299`; migrations applied through `012` |
| Production route checks | Backend and frontend health checks passed; protected Model Lab and long-document endpoints return `401` unauthenticated |
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
- Full understanding of scanned, handwritten, chart-heavy, signed, sealed, or image-heavy documents.
- Instant large-file analysis under unlimited concurrent OCR/PDF/XLS load.

## Current Product Decision

**Status:** Pilot-ready with disciplined validation.

BankAi is technically credible as an airgapped staff AI appliance, but it should still be expanded only after the pilot proves three things: staff save time, answers cite correct approved sources, and bank operators can maintain the system without heroic support.
