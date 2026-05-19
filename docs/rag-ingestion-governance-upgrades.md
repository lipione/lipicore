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
- Excel extraction preserves sheet names, merged ranges, and cell coordinates.
- HA deployment reference under `deploy/ha`.
- Docker Compose health checks cover Redis, backend, frontend, and nginx.
- `deploy/upgrade.sh` provides health-gated upgrades, optional backend tests, internal health checks, and public health checks.
- nginx uses Docker DNS re-resolution for backend/frontend upstreams after container replacement.

## Remaining Hard Problems

- Citation verification is lexical overlap, not a formal natural-language entailment model.
- OCR still depends on host image/PDF tooling and vision model quality.
- Complex charts, handwriting, seals, and signatures are still weak.
- Whole-bank HA still requires real external HA data services, not just Compose restart policies.
- Dependency pinning is still needed before release; current unpinned Python dependencies can pull very large Torch/CUDA wheels.
