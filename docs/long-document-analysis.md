# Queued Long-Document Analysis

Queued long-document analysis is the supported workflow for heavy OCR, large PDFs, and detailed Excel/PDF review. It exists so normal staff chat stays responsive while expensive extraction, context packing, and analyst-model generation run in the background.

## When To Use

Use this workflow for:

- Large policy PDFs, circular bundles, manuals, board packs, audit reports, and loan files.
- Scanned PDFs that may require OCR.
- Excel workbooks with many sheets, merged ranges, tables, formulas, and important cell references.
- Analysis requests that need a full document summary, exceptions list, key dates, staff action points, or detailed extraction.

Use normal chat or Ask Approved Knowledge for short policy questions where indexed source chunks are already enough.

## User Workflow

1. Upload the file in the Document Library or chat upload flow.
2. Wait for ingestion to reach `ready`, `indexed`, or `approved`, depending on the document scope and role.
3. In Document Library, choose `Queue analysis`.
4. Enter the analysis prompt.
5. LipiCore creates a background job and shows a status chip: queued, processing, packing context, generating, completed, or failed.
6. When complete, staff can open the stored result from the document row.

## Backend Flow

1. `POST /api/long-document-analysis` creates a `long_document_analysis_job` row.
2. The backend enqueues `process_long_document_analysis_job` on the existing Redis/RQ ingestion queue.
3. The worker reuses the extraction pipeline:
   - PDF text and table extraction through `pdfplumber` when available.
   - Open-source Tesseract OCR fallback for scanned PDFs up to `OCR_MAX_PAGES`.
   - Legacy Nepali PDF text-layer repair rerenders affected pages through OCR up to `OCR_TEXT_LAYER_REPAIR_MAX_PAGES`.
   - Excel extraction preserving sheet names, workbook dimensions, merged ranges, table ranges, formulas/cached values, and cell coordinates.
4. The worker uses `build_large_file_prompt` to select relevant page/sheet excerpts within `LLM_DEEP_CONTEXT_WINDOW_TOKENS`.
5. The analyst/deep model generates the result using a system prompt that requires source-backed analysis and forbids autonomous decisions.
6. Result text, metadata, progress, and errors are stored in PostgreSQL.

## API

```http
POST /api/long-document-analysis
GET /api/long-document-analysis?limit=100
GET /api/long-document-analysis/{job_id}
```

Create request:

```json
{
  "document_id": 123,
  "analysis_type": "long_document_analysis",
  "prompt": "Summarize the policy, extract key dates, exceptions, risks, and staff action points. Cite page or section labels where possible."
}
```

Response fields include:

- `status`: `queued`, `processing`, `packing_context`, `generating`, `completed`, or `failed`.
- `progress`: integer progress percentage.
- `result_text`: populated when completed.
- `error_message`: populated when failed.
- `metadata_json`: file type, selected context size, total pages/sheets, and excerpt packing metadata.

## Access Control

- Staff can queue and read their own jobs only.
- Staff can analyze approved global knowledge documents.
- Staff can analyze their own ready/indexed/approved session uploads.
- Bank admin, compliance, compliance officer, document reviewer, and super admin roles can analyze available bank documents and view bank-wide jobs.
- Disabled, archived, superseded, and failed documents are blocked.

## Operational Limits

Current defaults:

- Document Library upload limit: 50 MB.
- Chat upload limit: 50 MB.
- OCR engine: open-source Tesseract, configured by `OCR_ENGINE`, `OCR_LANGUAGES`, `OCR_TESSERACT_CONFIG`, and `OCR_IMAGE_DPI`.
- OCR fallback page cap: `OCR_MAX_PAGES=200`.
- Legacy Nepali text-layer repair cap: `OCR_TEXT_LAYER_REPAIR_MAX_PAGES=500`.
- Nepali PDFs with degraded embedded text layers can be repaired page-by-page with OCR when direct extraction corrupts vowel marks or common letters.
- OCR page Vision Review is optional and uses Qwen-VL only for separate visual notes on PDFs/images, capped by `OCR_VISION_REVIEW_MAX_PAGES=3`.
- Ingestion/analysis job timeout: `INGESTION_JOB_TIMEOUT_SECONDS=1800`.
- Default worker concurrency: `INGESTION_WORKER_CONCURRENCY=1`.
- Deep analysis context budget: `LLM_DEEP_CONTEXT_WINDOW_TOKENS`, default 8192 tokens.
- Deep analysis output cap: `LLM_DEEP_MAX_TOKENS`, default 768 tokens.

These are configuration limits, not quality guarantees. A 50 MB file may still be slow or low quality if it contains image-only pages, complex tables, charts, low-resolution scans, handwritten notes, seals, or signatures.

## Bank-Facing Boundary

Safe wording:

> LipiCore supports queued long-document analysis for large PDFs, Excel workbooks, and OCR-heavy files. It extracts and selects relevant excerpts, generates a staff-reviewable analysis, and stores the result with metadata. High-risk scanned, handwritten, stamped, signed, or complex-table content should be reviewed by staff before use.

Do not claim:

- Perfect OCR.
- Perfect table understanding.
- Signature, seal, or handwriting verification.
- Guaranteed regulatory correctness.
- Autonomous lending, compliance, or operational decisions.

## Monitoring

Operators should monitor:

- Redis queue depth and failed jobs.
- `ingestion-worker` heartbeat and logs.
- Job age by `long_document_analysis_job.status`.
- Disk growth for uploaded files and extracted artifacts.
- Deep model queue pressure and timeout rate.
- GPU memory before raising worker concurrency.

## Verification Before Bank Demo

Run at least one representative file from each bank category:

- Clean text PDF.
- Scanned PDF.
- Excel workbook with formulas and merged cells.
- Circular or SOP with tables.
- Nepali or bilingual document if the bank expects bilingual use.

Record whether the answer cited useful pages/sheets, whether low-confidence extraction was visible, and whether the result required staff correction.
