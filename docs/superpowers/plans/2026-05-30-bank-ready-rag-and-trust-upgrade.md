# Bank-Ready RAG And Trust Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden LipiCore from pilot-ready document chat into a bank-ready, source-grounded institutional AI platform.

**Architecture:** Keep the existing FastAPI, PostgreSQL, Qdrant, Redis/RQ, MinIO, and local vLLM architecture. Upgrade the system through small independently verifiable slices: ingestion quality, retrieval quality, answer trust, security controls, operational readiness, and bank-facing evaluation evidence.

**Tech Stack:** FastAPI, SQLModel/PostgreSQL, Qdrant, Redis/RQ, MinIO, vLLM, Tesseract OCR, pytest, React/Vite.

---

## Execution Strategy

This plan intentionally does not attempt a full platform rewrite. LipiCore already has the correct base shape: private deployment, approved-document RAG, document lifecycle, RBAC, source evidence, audit logs, and a RAG Evaluation Center. The upgrade should make that base safer and more measurable.

## Detailed Phase Plans

- Phase 2: `docs/superpowers/plans/2026-05-30-retrieval-precision-evaluation-gates.md`
- Phase 3: `docs/superpowers/plans/2026-05-30-prompt-injection-source-poisoning-defense.md`
- Phase 4: `docs/superpowers/plans/2026-05-30-citation-faithfulness.md`
- Phase 5: `docs/superpowers/plans/2026-05-30-ocr-table-review-workflow.md`
- Phase 6: `docs/superpowers/plans/2026-05-30-operational-bank-readiness.md`
- Phase 7: `docs/superpowers/plans/2026-05-30-product-ux-trust-layer.md`

### Phase 1: RAG Ingestion Quality

**Status:** Completed on 2026-05-30.

**Files:**
- Modified: `backend/app/services/ingestion_service.py`
- Modified: `backend/tests/test_ingestion_structure.py`

- [x] Add adaptive chunk profiles for default text, regulatory/section-heavy text, spreadsheets/tables, presentations, and OCR-heavy inputs.
- [x] Preserve page-level spreadsheet and slide labels as `section_label` metadata so citations can show `Sheet: ...` or `Slide ...`.
- [x] Wire document ingestion to choose chunk profiles from `file_type`, `document_type`, and OCR/section signals.
- [x] Add regression tests for spreadsheet chunk profile selection, sheet-label preservation, and compact OCR/image chunking.
- [x] Verify with `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_ingestion_structure.py -q`.

### Phase 2: Retrieval Precision And Evaluation Gates

**Priority:** Must-have before bank deployment.

- [ ] Add evaluation cases for each supported document class: circular, act/law, policy, SOP, scanned PDF, Excel workbook, and internal memo.
- [ ] Add retrieval metrics per case: expected source title, expected page/section/sheet, source recall, citation term recall, and not-found behavior.
- [ ] Add a release checklist requiring RAG Evaluation Center runs before changing embeddings, chunk profiles, prompts, model routes, or reranker settings.
- [ ] Create a small benchmark corpus under `docs/evaluations/fixtures/` using non-sensitive synthetic bank documents.

### Phase 3: Prompt-Injection And Source-Poisoning Defense

**Priority:** Must-have before bank deployment.

- [ ] Add document-ingestion warning flags for chunks containing instruction-like text such as "ignore previous instructions", "system prompt", or "do not cite".
- [ ] Wrap retrieved context with an explicit untrusted-source boundary in every RAG prompt.
- [ ] Add tests proving malicious retrieved text cannot change the source-backed refusal policy.
- [ ] Show source-risk warnings in the source evidence panel when a cited chunk contains instruction-like content.

### Phase 4: Citation Faithfulness

**Priority:** Must-have before broad rollout.

- [ ] Keep lexical citation verification as a cheap first pass.
- [ ] Add a second faithfulness checker for high-risk workflows that verifies each answer sentence against retrieved passages.
- [ ] Mark answers as `supported`, `partially_supported`, `unsupported_source`, or `not_found`.
- [ ] Block "official source-backed" badges when source support is partial or missing.

### Phase 5: OCR And Table Review Workflow

**Priority:** Must-have before selling heavy scanned-document claims.

- [ ] Add OCR quality buckets from existing `ocr_confidence`, `table_confidence`, and extraction flags.
- [ ] Make low-confidence OCR pages visible in the review queue.
- [ ] Add table-focused tests for merged cells, formulas, cached values, sheet names, and table ranges.
- [ ] Require staff review for low-confidence extracted text before using it as approved knowledge.

### Phase 6: Operational Bank Readiness

**Priority:** Must-have before production bank deployment.

- [ ] Add deployment evidence checklist for TLS, network isolation, secrets, backup/restore, Redis persistence, Qdrant snapshots, PostgreSQL backups, and model restart runbooks.
- [ ] Add queue-depth and GPU-capacity dashboards for model routes, ingestion workers, and long-document jobs.
- [ ] Require a customer-specific load test before claiming department or whole-bank capacity.
- [ ] Document rollback steps for backend, frontend, migrations, model route changes, and embedding collection changes.

### Phase 7: Product UX Trust Layer

**Priority:** Good to have for MVP, must-have for bank-wide adoption.

- [ ] Improve source viewer to show document title, page, section, sheet/slide label, chunk index, passage, relevance, OCR/table confidence, and verification status together.
- [ ] Add a clear "not found in approved sources" state with next actions.
- [ ] Add report-builder export that preserves source metadata and human-review status.
- [ ] Add department workspace presets for customer care, compliance, operations, credit administration, and audit.

## Commercial Boundary

Do not sell LipiCore as an autonomous lending, compliance, regulatory, or customer-impact decision engine. Sell the first bank-ready version as a private knowledge assistant and document intelligence appliance that answers from approved documents, shows evidence, keeps audit records, and requires staff review for final decisions.
