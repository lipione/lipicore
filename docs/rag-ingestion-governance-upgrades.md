# RAG, Ingestion, Governance, OCR, And HA Upgrades

## Implemented

- Real Redis/RQ ingestion queue with a separate `ingestion-worker` service.
- Configurable ingestion timeout, retry count, queue name, and worker concurrency.
- Document lifecycle state: `draft`, `approved`, `superseded`, `archived`, `disabled`.
- Chunk-level permission metadata copied from documents into both Postgres chunks and Qdrant payloads.
- Retrieval filters for approved global knowledge and ready session uploads.
- Hybrid retrieval now pulls a wider candidate set and reranks before building context.
- Citation verification checks answer sentences against retrieved source passages and adds verification metadata.
- Chat UI shows answer trust badges and a source evidence panel with full passage, page, section/chunk, relevance, and verification status.
- Evaluation Center UI at `/evaluations` lets bank admin, super admin, auditor, and data auditor roles run RAG quality checks.
- Document Library now exposes ingestion progress, lifecycle/readiness, and ready-for-chat state more clearly.
- AI Tasks now includes prompt readiness and review metadata so staff understand what context is being used.
- Scanned PDF fallback now OCRs up to `OCR_MAX_PAGES` instead of only the first 3 pages.
- PDF table extraction uses `pdfplumber` when available.
- Excel extraction preserves sheet names, workbook dimensions, merged ranges, named table ranges, formulas, cached values, and cell coordinates.
- Ingestion creates page-level extraction review records so low OCR/table/layout confidence can appear in the Document Review queue.
- File analysis now packs relevant page/section excerpts into the model context instead of truncating to the first few thousand characters.
- Heavy OCR and very large Excel/PDF analysis now runs as queued long-document jobs with status polling, relevance-based excerpt packing, and stored results for staff review.
- Detailed workflow reference: `docs/long-document-analysis.md`.
- Staff decision-support workspaces now exist for Support Desk, Compliance Workspace, Loan Support, Document Review, and Model Lab.
- Fast and analyst model routes now have separate context-window settings: `LLM_FAST_CONTEXT_WINDOW_TOKENS` and `LLM_DEEP_CONTEXT_WINDOW_TOKENS`.
- Current production routes all text lanes to the Gemma 4 26B endpoint and uses Qwen3-VL for vision/OCR; the optional fast text endpoint is disabled until GPU capacity is rebalanced.
- HA deployment reference under `deploy/ha`.
- Docker Compose health checks cover Redis, backend, frontend, and nginx.
- `deploy/upgrade.sh` provides health-gated upgrades, optional backend tests, internal health checks, and public health checks.
- nginx uses Docker DNS re-resolution for backend/frontend upstreams after container replacement.

## Remaining Hard Problems

- Citation verification is lexical overlap, not a formal natural-language entailment model.
- OCR still depends on host image/PDF tooling and vision model quality.
- Complex charts, handwriting, seals, and signatures are still weak.
- Larger context windows require a deployed model endpoint that actually supports the configured context length.
- Queued long-document analysis reduces chat blocking, but it still depends on OCR quality, worker capacity, deep-model queue load, and selected-excerpt relevance.
- Whole-bank HA still requires real external HA data services, not just Compose restart policies.
- Dependency pinning is still needed before release; current unpinned Python dependencies can pull very large Torch/CUDA wheels.
