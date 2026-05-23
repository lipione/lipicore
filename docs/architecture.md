# Architecture

The Bank's Own LLM architecture is designed around isolation, security, and the Retrieval-Augmented Generation (RAG) pattern.

## Components
1. **Frontend (React + Vite):** A static SPA served by Nginx. Communicates exclusively with the Backend API.
2. **Backend (FastAPI):** The core orchestration layer. Handles Auth, RBAC, document ingestion orchestration, and RAG prompt construction.
3. **PostgreSQL:** Stores relational metadata: Users, Banks, Document Metadata, Chat History, and Audit Logs.
4. **MinIO:** S3-compatible object storage for storing raw uploaded documents securely.
5. **Qdrant:** Vector database storing text chunk embeddings with payload metadata (bank_id, document_id) for precise, isolated retrieval.
6. **Redis:** Admission-control state for local model concurrency and RQ-backed document ingestion.
7. **LLM Engine:** Local vLLM model servers exposed through OpenAI-compatible endpoints. The repository supports separate text and vision routes; the current production server routes all text lanes to Gemma 4 26B and uses Qwen3-VL for vision/OCR.
8. **Ingestion Worker:** Extracts text/tables/OCR output, chunks content, embeds chunks, and indexes PostgreSQL/Qdrant outside the API process.
9. **Long-Document Analysis Jobs:** Redis/RQ-backed background jobs for heavy OCR, large PDFs, and detailed Excel/PDF review.
10. **Evaluation Center:** Frontend and API workflow for running bank-specific RAG quality tests.

## Data Flow (Chat)
1. User submits query.
2. Backend authenticates user and determines `bank_id` and role permissions.
3. Query is embedded using Sentence-Transformers.
4. Hybrid retrieval combines Qdrant vector search with PostgreSQL full-text search, filtered by `bank_id`, scope, session, and role.
5. Backend verifies document access levels and drops low-relevance results before context construction.
6. Retrieved candidates are reranked so the model receives fewer but more relevant chunks.
7. Context is sent to the selected vLLM model tier through the local LLM gateway.
8. LLM response, source snippets, full source passages, and metadata are saved to DB and returned to the user.
9. Citation verification metadata is computed from the generated answer and retrieved source passages.

## Data Flow (Document Ingestion)

1. User uploads a document from Chat, Document Library, or AI Tasks.
2. Backend stores the original file in MinIO and metadata in PostgreSQL.
3. Backend enqueues a Redis/RQ ingestion job.
4. The ingestion worker extracts text, OCR output, PDF tables, spreadsheet sheet/cell metadata, and presentation text.
5. Extracted content is chunked and embedded.
6. Chunks are written to PostgreSQL and Qdrant with `bank_id`, document lifecycle, document scope, and permission metadata.
7. The UI shows queued, extracting, embedding, indexing, ready, or failed status.

## Data Flow (Queued Long-Document Analysis)

1. User opens a ready/indexed/approved document in the Document Library and chooses `Queue analysis`.
2. Backend validates bank, role, document scope, document lifecycle, and job ownership.
3. Backend stores a `long_document_analysis_job` row and enqueues work on Redis/RQ.
4. The worker extracts PDF text/tables, OCR output, spreadsheet sheet/cell metadata, or presentation text using the same ingestion extraction layer.
5. `build_large_file_prompt` selects relevant page/sheet excerpts within the configured deep-model context budget.
6. The analyst model generates a staff-reviewable result using only selected excerpts.
7. PostgreSQL stores progress, result text, errors, and excerpt-packing metadata.
8. The UI polls `GET /api/long-document-analysis` and shows queued, processing, packing context, generating, completed, or failed status.

See `docs/long-document-analysis.md` for API details, access rules, and operating limits.

## Trust And Evaluation

- Sources are shown only when they pass relevance and access filters.
- The source evidence panel exposes the exact passage used by the answer, not only a document title.
- RAG evaluation sets can be submitted to `POST /api/evaluations/rag` or through `/evaluations`.
- Evaluation scores cover expected source recall, citation term recall, answer term recall, and expected not-found behavior.
- Evaluation access is limited to analytics-capable roles: super admin, bank admin, auditor, and data auditor.

## Current Limits

- Citation verification is lexical overlap, not a formal entailment model.
- Long, broad multi-document answers should use the queued long-document workflow; true cross-document map-reduce synthesis still needs more work.
- Scanned, handwritten, chart-heavy, seal-heavy, and signature-heavy files remain weak.
- The current production server does not run the optional fast 4B text endpoint; all text lanes share the 26B endpoint, so concurrency limits must be sized against that single GPU.
- Single-host Compose is a pilot architecture. Whole-bank deployment needs HA PostgreSQL, object storage, vector storage, Redis, backend replicas, and inference redundancy.
