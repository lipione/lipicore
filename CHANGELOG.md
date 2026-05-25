# Changelog

## 2026-05-25

- Replaced the visible Support Desk, Loan Support, and Document Review product pages with a focused OCR Extraction page.
- Added `POST /api/ocr/extract` for transient text extraction from supported files without creating document records or indexing them into approved knowledge.
- Added CSV extraction support to the shared ingestion/extraction path.
- Redirected old frontend workflow URLs to `/ocr` and updated dashboard/sidebar entry points.
- Added backend OCR API tests for successful TXT extraction and unsupported file rejection.
- Added optional OCR Vision Review: Qwen-VL can add separate review notes for PDF/image uploads after open-source OCR, capped by `OCR_VISION_REVIEW_MAX_PAGES`.

## 2026-05-23

- Deployed the bank staff AI upgrade to the remote production path `/data/bankai` at commit `615d299`.
- Applied Alembic migrations through `012`, including document freshness/confidence, support cases, compliance reviews, loan support, document extraction review pages, and queued long-document analysis jobs.
- Rebuilt and recreated app services while preserving production `docker-compose.yml`, `.env`, nginx, certificates, and running GPU model containers.
- Documented the current production model profile:
  - All text routes (`LLM_A`, `LLM_B`, `LLM_C`) route to `lipicore-vllm-c` / Gemma 4 26B 4-bit.
  - Vision/OCR routes use `lipicore-vllm-vision` / Qwen3-VL 8B.
  - `lipicore-vllm-b` is not running and should not be started without a GPU capacity decision.
- Verified remote health checks for backend, frontend, and protected API routes after deployment.

## 2026-05-21

- Added queued long-document analysis for heavy OCR, large PDFs, and detailed Excel/PDF review:
  - New `long_document_analysis_job` table and Alembic migration.
  - New `/api/long-document-analysis` create/list/get endpoints.
  - Redis/RQ worker job that extracts content, packs relevant excerpts, calls the analyst model, and stores the result.
  - Document Library UI for queueing analysis, polling job status, and viewing completed results.
  - Staff users see only their own analysis jobs; bank admin/compliance/document reviewer roles can view bank-wide jobs.
- Updated documentation for product positioning, architecture, deployment, sizing, security, pilot scope, demo flow, and sales-safe large-file claims.
- Verification:
  - Backend workflow/document/long-analysis slice: `14 passed`.
  - Frontend build passed.
  - Frontend lint passed with 0 errors and existing e2e console warnings only.
  - `git diff --check` passed.

## 2026-05-19

- Upgraded BankAi into a stronger airgapped bank AI appliance baseline:
  - Added Redis/RQ document ingestion with a separate `ingestion-worker`.
  - Added document lifecycle states, chunk-level permission metadata, and approved/superseded/disabled retrieval filtering.
  - Added hybrid retrieval reranking and citation verification metadata.
  - Expanded OCR/table extraction for PDFs and spreadsheets.
  - Added RAG evaluation API and frontend Evaluation Center.
  - Added source passage viewer with page/section/chunk/relevance metadata.
  - Added visible answer trust and citation verification badges in chat.
  - Improved Document Library ingestion status and ready-for-chat visibility.
  - Improved AI Tasks guided workflow with prompt readiness and review metadata.
  - Added model capacity analytics for fast/deep local vLLM tiers.
  - Added Docker health checks and `deploy/upgrade.sh` for health-gated upgrades.
- Tightened backend access control for analytics, model-capacity telemetry, and RAG evaluations.
- Fixed nginx upstream resolution by using Docker DNS re-resolution for backend/frontend containers.
- Verified on the remote test server:
  - `npm run build`
  - `npm run lint` with zero errors and existing e2e console warnings only
  - remote backend tests: `37 passed`
  - public smoke checks for `/health`, `/chat`, `/documents`, `/tasks`, `/analytics`, and `/evaluations`

## 2026-05-07

- Fixed the chat shell for mobile by replacing the always-pinned sidebar with a responsive drawer and mobile-safe top bar.
- Updated chat controls to match the deployed clean Gemma 4 vLLM runtime: fast 4B and analyst/report 26B.
- Allowed ready uploaded documents to remain queryable while unrelated session uploads are still processing.
- Tightened RAG retrieval so uploaded-document questions do not automatically cite unrelated global documents.
- Preserved real message timestamps and fixed stopped-generation partial response handling.
- Replaced overclaimed "Encrypted End-to-End" UI copy with "Encrypted in transit".
- Switched the frontend icon font to Material Symbols Outlined.
- Replaced the default Vite favicon reference with an inline BankAi favicon.
- Updated Playwright config and chat e2e tests to use env-driven base URL and credentials with installed Chrome.

Verification:

- `npm run lint`
- `npm run build`
- `python -m py_compile backend\app\api\chat.py backend\app\services\rag_service.py`
- Local Chrome smoke screenshots for desktop and mobile chat layouts.

## 2026-04-28

- Completed BankAi recovery audit and documented current frontend, backend, database, Docker, and test state in `RESUME_REPORT.md`.
- Fixed local backend import/test failure by moving upload directory creation out of module import and into request-time helpers.
- Added configurable upload paths through `UPLOAD_DIR` and `CHAT_UPLOAD_DIR`, defaulting to the OS temp directory for local development.
- Fixed active session upload restoration for staff users by allowing `/api/documents` to return the current user's non-disabled `session_upload` documents alongside approved global documents.
- Sanitized chat audit metadata and prompt-injection security metadata so masked queries are stored instead of raw user input.
- Added focused backend tests for session upload reload behavior and session-first RAG priority over global knowledge.

Verification:

- `python -m py_compile app\api\chat.py app\api\documents.py app\services\rag_service.py app\services\guardrail_service.py`
- `python -m pytest tests\test_main.py tests\test_session_documents.py -p no:cacheprovider`
- `npm run build`
