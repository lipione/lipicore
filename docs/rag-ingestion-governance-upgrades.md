# RAG, Ingestion, Governance, OCR, And HA Upgrades

## Implemented

- Real Redis/RQ ingestion queue with a separate `ingestion-worker` service.
- Configurable ingestion timeout, retry count, queue name, and worker concurrency.
- Document lifecycle state: `draft`, `approved`, `superseded`, `archived`, `disabled`.
- Chunk-level permission metadata copied from documents into both Postgres chunks and Qdrant payloads.
- Retrieval filters for approved global knowledge and ready session uploads.
- Hybrid retrieval now pulls a wider candidate set and reranks before building context.
- Citation verification checks answer sentences against retrieved source passages and adds verification metadata.
- Policy citation metadata now captures PDF page, printed page when present, document heading, clause number, citation confidence, and incomplete reasons on chunks and Qdrant payloads.
- Policy-like answers require PDF page, document heading, and clause number; missing required fields return a citation-incomplete review response instead of final policy advice.
- Existing approved documents can be updated with document-level citation backfill.
- Chat UI shows answer trust badges and a source evidence panel with full passage, document heading, clause, PDF page, printed page, section metadata, relevance, and verification status.
- Evaluation Center UI at `/evaluations` lets bank admin, super admin, auditor, and data auditor roles run RAG quality checks.
- Evaluation cases can now score expected document headings, clause numbers, printed page numbers, and PDF page aliases.
- Document Library now exposes ingestion progress, lifecycle/readiness, and ready-for-chat state more clearly.
- AI Tasks now includes prompt readiness and review metadata so staff understand what context is being used.
- Scanned PDF fallback now OCRs up to `OCR_MAX_PAGES` instead of only the first 3 pages.
- Legacy Nepali PDF text layers are detected and repaired through open-source OCR instead of indexing Preeti/Kantipur-style ASCII glyph text.
- PDF table extraction uses `pdfplumber` when available.
- Excel extraction preserves sheet names, workbook dimensions, merged ranges, named table ranges, formulas, cached values, and cell coordinates.
- Ingestion creates page-level extraction metadata so low OCR/table/layout confidence can be audited or used by future review workflows.
- File analysis now packs relevant page/section excerpts into the model context instead of truncating to the first few thousand characters.
- Heavy OCR and very large Excel/PDF analysis now runs as queued long-document jobs with status polling, relevance-based excerpt packing, and stored results for staff review.
- Detailed workflow reference: `docs/long-document-analysis.md`.
- The visible product surface now emphasizes OCR Extraction, Compliance Workspace, Model Lab, RAG Evaluation, and queued long-document analysis.
- The visible product surface now also includes optional internal banking workspaces: Employee Search, Staff Inbox, CEO's Message, Notifications & Alerts, Forex/Time/Dates, Knowledge Gaps, Policy Changes, Audit Evidence Packs, and banking workflow helpers.
- Super Admin feature controls can turn the new internal workspace features on or off per bank; all new feature flags default off.
- Market utilities show local banking time, business date, and bank-published exchange-rate batches that Treasury/admin users can update 2-3 times per business day.
- Fast and analyst model routes now have separate context-window settings: `LLM_FAST_CONTEXT_WINDOW_TOKENS` and `LLM_DEEP_CONTEXT_WINDOW_TOKENS`.
- Current production routes all text lanes through LipiCore. OCR extraction uses open-source Tesseract plus direct parsers by default; LipiCore remains available for separate document-image analysis where enabled. The optional LipiFast endpoint is disabled until GPU capacity is rebalanced.
- HA deployment reference under `deploy/ha`.
- Docker Compose health checks cover Redis, backend, frontend, and nginx.
- `deploy/upgrade.sh` provides health-gated upgrades, optional backend tests, internal health checks, and public health checks.
- nginx uses Docker DNS re-resolution for backend/frontend upstreams after container replacement.

## Remaining Hard Problems

- Citation verification runs a lexical overlap precheck then applies configurable semantic matching when enabled. It is not presented as formal legal entailment.
- OCR still depends on host image/PDF tooling, Tesseract language packs, and source scan quality.
- Complex charts, handwriting, seals, and signatures are still weak.
- Larger context windows require a deployed model endpoint that actually supports the configured context length.
- Queued long-document analysis reduces chat blocking, but it still depends on OCR quality, worker capacity, deep-model queue load, and selected-excerpt relevance.
- Whole-bank HA still requires real external HA data services, not just Compose restart policies.
- Dependency pinning is still needed before release; current unpinned Python dependencies can pull very large Torch/CUDA wheels.
- Internal workspace helpers are operational aids and drafts; maker-checker, compliance, and customer-impact approvals still remain with authorized bank staff.
