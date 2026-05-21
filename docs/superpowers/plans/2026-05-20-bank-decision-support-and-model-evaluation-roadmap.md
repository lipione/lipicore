# LipiCore Bank Decision Support And Model Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn bank-requested claims into controlled, auditable LipiCore modules without claiming autonomous lending, compliance replacement, guaranteed regulatory correctness, perfect OCR, blanket HA/SLA, or general superiority to GPT-4/GPT-5.

**Architecture:** Keep the current FastAPI, React/Vite, PostgreSQL, Qdrant, Redis/RQ, MinIO, nginx, and vLLM stack. Add workflow modules for customer care, compliance, lending support, document intelligence, model evaluation, and HA/SLA evidence. Every high-risk output must carry source evidence, confidence, limitations, and human approval state.

**Tech Stack:** FastAPI, SQLModel, Alembic, PostgreSQL, Qdrant, Redis/RQ, MinIO, React/Vite, Tailwind, vLLM, optional SGLang/TensorRT-LLM lab runtimes, pytest, Playwright, Locust.

---

## Current Baseline

LipiCore already has the right base for a bank staff appliance:

- Staff chat modes and model mode selector.
- vLLM fast/deep model routes with Redis admission control.
- Document upload, async ingestion, OCR/table extraction hooks, chunking, embeddings, Qdrant indexing.
- Approved document lifecycle and chunk-level permission metadata.
- RAG source evidence panel, citation verifier, and Evaluation Center.
- Load tests for 25/50/100 active-staff claims.
- Pilot, department, and whole-bank sizing docs.
- HA reference compose under `deploy/ha`.

Main gap: the product still needs deeper domain workflows, stronger evaluation evidence, long-document benchmark evidence, OCR confidence/review maturity, model benchmark harnesses, and deployment-tier proof before we can safely answer aggressive bank requests.

## Sales Positioning To Use Now

Use this wording in bank replies:

> LipiCore is an airgapped AI staff-assistance and decision-support appliance. It helps bank staff find, understand, summarize, extract, compare, and draft from approved bank knowledge and uploaded internal files. It does not make final lending, compliance, regulatory, or operational decisions. Final decisions remain with authorized bank staff.

Use this capability ladder:

- Today: staff AI helpdesk, approved-knowledge Q&A, document analysis, drafting, summarization, audit trail.
- Pilot: customer care, branch support, compliance lookup, controlled internal file analysis.
- Next phase: lending support, compliance review, OCR confidence workflow, supervisor approval.
- Later: HA whole-bank deployment, model benchmark evidence, specialized extraction and long-document reasoning.

## Claims Matrix

| Bank asks for | Safe product language | Required module before stronger claim |
| --- | --- | --- |
| Lending decisions | Decision support for lending staff; final approval remains with officers. | Loan file workspace, checklist, risk summary, credit memo draft, maker-checker approval. |
| Compliance officer replacement | Reduces compliance lookup and drafting workload; officers still review and approve. | Compliance workspace, circular impact review, policy gap notes, approval queue. |
| Guaranteed regulatory correctness | Source-backed and auditable answers from bank-approved documents; document freshness remains bank-governed. | Effective dates, superseded states, mandatory citations, citation verifier, regulatory eval suite. |
| Perfect scanned PDF/table/seal/signature/handwriting understanding | OCR and extraction with confidence scores and human review for low-confidence pages. | Full OCR, layout parsing, table extraction, page viewer, confidence and review queue. |
| Production HA/SLA for all banks | SLA depends on selected deployment tier and tested infrastructure. | HA Postgres, Qdrant cluster, Redis HA, GPU replicas, monitoring, restore drills. |
| Better than GPT-4/GPT-5 | Better for private bank knowledge inside an airgapped, auditable environment. | Side-by-side bank evals, latency tests, citation accuracy, bilingual evaluation sets. |

## Research Snapshot

Use primary docs and model cards before downloading or claiming support:

- vLLM supports high-throughput serving, PagedAttention, continuous batching, quantization, speculative decoding, chunked prefill, streaming, OpenAI-compatible APIs, prefix caching, metrics, and distributed inference. Source: https://docs.vllm.ai/en/v0.7.3/
- vLLM latest server options include performance modes and structured output config. Source: https://docs.vllm.ai/en/latest/cli/serve/
- SGLang is worth testing for Qwen/DeepSeek/Gemma/Mistral long-context and prefix-cache-heavy workloads because it supports RadixAttention, prefix caching, chunked prefill, continuous batching, quantization, and OpenAI-compatible APIs. Source: https://docs.sglang.io/
- TensorRT-LLM is the enterprise NVIDIA performance path for high-throughput and high-concurrency deployments, especially when banks buy H100/H200/B200/GB200-class hardware. Source: https://nvidia.github.io/TensorRT-LLM/
- Qwen3.6 supports vLLM and SGLang deployment; Qwen3.6-35B-A3B examples use 262K context with tensor parallelism. Source: https://github.com/QwenLM/Qwen3.6
- Qwen3-30B-A3B-Instruct-2507 is a strong long-context candidate: 30.5B total, 3.3B active, 262K native context, and 1M-token configuration with high GPU memory requirements. Source: https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507
- Meta Llama 4 Scout is a multimodal MoE candidate with a very large context window, but license and local runtime behavior must be validated before bank packaging. Source: https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct
- Mistral 3 offers open Apache-2.0 models from edge sizes to Mistral Large 3; Large 3 is a large MoE meant for serious infrastructure, not pilot appliances. Source: https://mistral.ai/news/mistral-3
- Mistral Small 3.2 is deprecated in favor of Mistral Small 4 after April 30, 2026, so do not start a new bank benchmark on Small 3.2 unless comparing legacy behavior. Source: https://docs.mistral.ai/models/overview
- Gemma 3 official Google docs state 4B/12B/27B support 128K input context; Gemma 4 official Google Hugging Face cards now exist and should be verified directly before demo claims. Sources: https://ai.google.dev/gemma/docs/core and https://huggingface.co/google/gemma-4-E4B
- DeepSeek V3.2 is 671B total and 37B active, MIT licensed, 128K context, and useful as a high-end benchmark/reference model; it is too large for default bank appliance packaging. Sources: https://api-docs.deepseek.com/news/news251201 and https://fe-static.deepseek.com/chat/transparency/deepseek-v3.2-model-card-0414-EN.pdf
- BGE-M3 and Jina Embeddings v3 are strong multilingual embedding baselines with 8192-token context. Sources: https://huggingface.co/BAAI/bge-m3 and https://huggingface.co/jinaai/jina-embeddings-v3
- Qwen3 Embedding/Reranker models are strong multilingual retrieval candidates in 0.6B/4B/8B sizes. Source: https://github.com/QwenLM/Qwen3-Embedding
- Qdrant recommends replicated 3+ node clusters for production resilience. Source: https://qdrant.tech/documentation/guides/distributed_deployment/
- Redis Sentinel provides monitoring, notification, automatic failover, and client configuration provider behavior for Redis HA. Source: https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/
- PostgreSQL official HA documentation covers streaming replication and standby servers. Source: https://www.postgresql.org/docs/16/high-availability.html

## Model Candidates To Test

Do not standardize on a model by reputation. Standardize by bank evaluation score, latency, cost, hardware fit, license, and deployment stability.

### Fast Staff Chat Tier

Goal: high concurrency, short answers, customer-care drafts, branch staff Q&A, translation, simple summaries.

- Current baseline: Gemma 4 E4B/4B-style fast tier already configured in compose.
- Test next: Gemma 4 E4B-it, Ministral 3 8B or 14B, Qwen3.5 9B/4B if available in approved model registry, Qwen3-4B-Instruct-2507.
- Required metrics: first token latency, full answer latency, tokens/sec, GPU memory, 20/40/75 concurrent streams, Nepali/English answer quality, not-found discipline.

### Analyst Tier

Goal: compliance explanation, policy comparison, risk factors, credit memo draft, complex customer cases.

- Current baseline: Gemma 4 26B 4-bit-style deep tier.
- Test next: Qwen3.6-27B, Qwen3.6-35B-A3B, Qwen3-30B-A3B-Instruct-2507, Gemma 4 26B-A4B-it, Gemma 4 31B-it, Mistral Small 4.
- Required metrics: citation usefulness, answer correctness, reasoning stability, bilingual terminology, output structure, tail latency under queue pressure.

### Long-Document Tier

Goal: large policies, circular bundles, loan files, audit reports, multi-document comparison.

- Best test priority: Qwen3-30B-A3B-Instruct-2507 because its official card documents 262K native context and a 1M-token configuration path.
- Also test: Qwen3.6-35B-A3B, Llama 4 Scout, Gemma 4 31B/26B, DeepSeek V3.2 only on high-end infrastructure.
- Required architecture: do not send raw 500-page files directly by default. Use queued long-document jobs, relevance-based excerpt packing, map-reduce where needed, source tables, selective retrieval, and final synthesis.

### Vision/OCR Tier

Goal: scanned PDFs, tables, forms, stamps/seals/signature detection, image-based source evidence.

- Test: Gemma 4 E4B/26B/31B multimodal, Llama 4 Scout, Qwen3-VL and Qwen3-VL-Reranker where runtime support is stable.
- Keep handwriting and signature verification as detection/flagging, not legal authentication.
- Required metrics: OCR character error rate, table cell accuracy, page-level confidence, false positive/negative rate for stamp/signature/handwriting flags.

### Embedding And Reranking Tier

Goal: better retrieval for English/Nepali, circulars, policies, product docs, and long files.

- Replace or benchmark against current `all-MiniLM-L6-v2`.
- Test embeddings: BAAI/bge-m3, jinaai/jina-embeddings-v3, Qwen/Qwen3-Embedding-0.6B, Qwen/Qwen3-Embedding-4B, Qwen/Qwen3-Embedding-8B.
- Test rerankers: BAAI/bge-reranker-v2-m3, Qwen/Qwen3-Reranker-0.6B, Qwen/Qwen3-Reranker-4B, Qwen/Qwen3-Reranker-8B.
- Required metrics: source recall@5, citation term recall, answer term recall, not-found pass rate, Nepali exact-term retrieval, latency overhead.

## Phase 0: Bank Reply And Demo Readiness

**Timeline:** 3-5 working days.

**Outcome:** We can reply banks with confidence without overclaiming.

**Files:**
- Create: `docs/proposals/lipicore-bank-safe-capability-matrix.md`
- Create: `docs/proposals/lipicore-bank-pilot-scope-template.md`
- Modify: `frontend/src/pages/Landing.jsx`
- Modify: `frontend/src/pages/Features.jsx`
- Modify: `BankAi/README.md`

- [x] Write the public capability matrix using the safe claims table above.
- [x] Remove or soften any UI copy that says or implies 99.9% handwriting accuracy, final compliance validation, autonomous loan approval, or better-than-GPT claims.
- [x] Add a bank pilot scope template: 20-50 users, 200-500 approved documents, 30 days, customer care/branch/compliance lookup.
- [x] Add a demo script with three flows: Ask BankAi, Ask Approved Knowledge, Analyze Internal File.
- [x] Add a one-page "what LipiCore does not do" statement for procurement and risk teams.
- [x] Verification: run `rg -n "99.9|guarantee|guaranteed|replace|autonomous|lending decision|better than GPT|handwritten|signature" BankAi/frontend BankAi/docs BankAi/README.md`.

## Phase 1: Trust Foundation Closure

**Timeline:** 2-3 weeks.

**Outcome:** Source-backed answers are clearer, stricter, measurable, and auditable.

**Files:**
- Modify: `backend/app/models/document.py`
- Create: `backend/alembic/versions/007_document_freshness_and_confidence.py`
- Modify: `backend/app/schemas/document.py`
- Modify: `backend/app/services/rag_service.py`
- Modify: `backend/app/services/citation_verifier.py`
- Modify: `backend/app/services/rag_evaluation_service.py`
- Modify: `backend/app/api/documents.py`
- Modify: `backend/app/api/evaluations.py`
- Modify: `frontend/src/pages/Documents.jsx`
- Modify: `frontend/src/pages/EvaluationCenter.jsx`
- Modify: `frontend/src/components/chat/AnswerTrustBadge.jsx`
- Modify: `frontend/src/components/chat/SourceEvidencePanel.jsx`
- Test: `backend/tests/test_rag_evaluation.py`
- Test: `backend/tests/test_session_documents.py`
- Test: `frontend/tests/e2e/session-rag-working.spec.js`

- [x] Add document freshness metadata: `effective_from`, `effective_to`, `regulator`, `jurisdiction`, `superseded_reason`, `review_due_at`, `approved_by`.
- [x] Add chunk metadata: extraction confidence, OCR confidence, table confidence, page bbox coordinates where available.
- [x] Extend Evaluation Center to support answer-type gates: `source_required`, `not_found_required`, `citation_required`, `no_general_policy_advice`.
- [x] Upgrade citation verifier from lexical overlap only to a two-stage verifier: lexical precheck plus optional local NLI/entailment model in offline batch mode.
- [x] Add a strict compliance/policy answer mode: no answer unless an approved source supports it.
- [x] Show "unsupported by approved source" distinctly from "general answer".
- [x] Add document freshness warnings when a source is expired, due for review, or superseded.
- [x] Add bank-specific evaluation seed packs: customer care, branch operations, compliance circulars, product FAQs, lending policy.
- [ ] Verification: run backend pytest for RAG and session documents, frontend build, Playwright session RAG flow.
  - 2026-05-21: backend RAG/session pytest passed, frontend build passed, frontend lint passed with existing e2e console warnings. Playwright session RAG flow is blocked until `PLAYWRIGHT_ADMIN_PASSWORD` is available.
  - 2026-05-21: citation verifier, model-lab tools, seed packs, RAG evaluation, and session document tests passed locally. Remote model inventory and baseline model smoke/concurrency benchmarks completed through SSH tunnels.

## Phase 2: Customer Care And Branch Support Workflow

**Timeline:** 2-3 weeks after Phase 1.

**Outcome:** The first pilot workflow is operational, not just a chat demo.

**Files:**
- Create: `backend/app/models/support_case.py`
- Create: `backend/app/schemas/support_case.py`
- Create: `backend/app/services/support_case_service.py`
- Create: `backend/app/api/support_cases.py`
- Modify: `backend/app/main.py`
- Create: `backend/alembic/versions/008_support_case_workspace.py`
- Modify: `backend/app/services/task_service.py`
- Create: `frontend/src/pages/SupportDesk.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Create: `backend/tests/test_support_case_service.py`
- Create: `frontend/tests/e2e/support-desk.spec.js`

- [x] Add support case records: customer issue category, channel, priority, staff owner, status, source docs, draft response, escalation target.
- [ ] Add guided tasks: failed transaction response, card dispute response, KYC/account servicing answer, complaint escalation note.
- [x] Require generated customer replies to include "staff review required" metadata.
- [ ] Add supervisor escalation action: assign case, add note, export draft.
- [ ] Add per-case audit log: prompt, selected docs, answer metadata, staff edits, export event.
- [ ] Add dashboard metrics: answer accepted, edited, escalated, no-source, response time.
- [ ] Verification: 25-case pilot eval with approved customer-care SOPs and 10 no-source traps.
  - 2026-05-21: Support case API/service/frontend foundation added. Pilot eval, guided task generation, and export/audit workflow remain release gates.

## Phase 3: Compliance Workspace

**Timeline:** 3-5 weeks after Phase 1.

**Outcome:** Compliance officers get a review tool, not replacement messaging.

**Files:**
- Create: `backend/app/models/compliance_review.py`
- Create: `backend/app/schemas/compliance_review.py`
- Create: `backend/app/services/compliance_review_service.py`
- Create: `backend/app/api/compliance_reviews.py`
- Modify: `backend/app/main.py`
- Create: `backend/alembic/versions/009_compliance_review_workspace.py`
- Modify: `frontend/src/pages/ComplianceRisk.jsx`
- Create: `frontend/src/pages/ComplianceWorkspace.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Create: `backend/tests/test_compliance_review_service.py`
- Create: `frontend/tests/e2e/compliance-workspace.spec.js`

- [x] Add circular impact summary: what changed, affected departments, deadlines, staff actions, source citations.
- [ ] Add policy gap detector: compare new circular against approved internal policies and list likely gaps with citations.
- [ ] Add compliance checklist generator: obligations, evidence required, owner, due date, status.
- [x] Add review/approval queue: draft, under review, approved, returned, archived.
- [ ] Add audit export: source docs, generated summary, reviewer comments, approval trail.
- [ ] Add "not legal/regulatory guarantee" disclaimer in metadata and export footer.
- [ ] Verification: compliance eval pack must pass source recall, citation recall, not-found traps, and stale-source warning tests.
  - 2026-05-21: Compliance review API/service/frontend foundation added with officer-review status and non-guarantee disclaimer. Gap detection and audit export remain release gates.

## Phase 4: Lending Decision-Support Workspace

**Timeline:** 4-6 weeks after Phase 1.

**Outcome:** LipiCore can credibly support lending teams without making lending decisions.

**Files:**
- Create: `backend/app/models/loan_support.py`
- Create: `backend/app/schemas/loan_support.py`
- Create: `backend/app/services/loan_support_service.py`
- Create: `backend/app/api/loan_support.py`
- Modify: `backend/app/main.py`
- Create: `backend/alembic/versions/010_loan_support_workspace.py`
- Create: `frontend/src/pages/LoanSupport.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Create: `backend/tests/test_loan_support_service.py`
- Create: `frontend/tests/e2e/loan-support.spec.js`

- [x] Add loan file workspace: applicant profile, loan type, requested amount, collateral, uploaded documents, assigned officer, status.
- [x] Add required-document checklist templates by loan/product type.
- [x] Add missing-document detector from uploaded files and staff-filled fields.
- [ ] Add policy eligibility check with citations and "human review required" outcome.
- [x] Add risk factor extraction: income inconsistency, collateral gaps, expired docs, policy exceptions, missing KYC/AML evidence.
- [x] Add credit memo draft: borrower summary, facility request, collateral, policy checklist, risks, open questions, recommendation field left blank by default.
- [ ] Add maker-checker approval workflow: maker draft, checker review, returned changes, approved for committee packet.
- [x] Ensure system never emits final approve/reject as an automated decision.
- [ ] Verification: loan eval pack with at least 50 cases, including missing-doc, conflicting-info, unsupported-policy, and no-source scenarios.
  - 2026-05-21: Loan support API/service/frontend foundation added. It stores missing documents, risk factors, memo drafts, and keeps `automated_decision` unset.

## Phase 5: Document Intelligence And Extraction Confidence

**Timeline:** 4-8 weeks. Can run partly in parallel with Phases 3 and 4.

**Outcome:** Scanned and complex documents become reviewable, not magically "understood."

**Files:**
- Modify: `backend/app/services/ingestion_service.py`
- Create: `backend/app/services/document_intelligence_service.py`
- Create: `backend/app/services/table_extraction_service.py`
- Create: `backend/app/services/ocr_confidence_service.py`
- Modify: `backend/app/models/document.py`
- Create: `backend/alembic/versions/011_document_extraction_confidence.py`
- Modify: `backend/app/api/documents.py`
- Create: `frontend/src/pages/DocumentReview.jsx`
- Modify: `frontend/src/pages/Documents.jsx`
- Modify: `frontend/src/components/chat/SourceEvidencePanel.jsx`
- Create: `backend/tests/test_document_intelligence_service.py`
- Create: `backend/tests/test_ingestion_structure.py`
- Create: `frontend/tests/e2e/document-review.spec.js`

- [x] Store page-level extraction records: text, tables, OCR confidence, parser, page image reference, bbox metadata.
- [ ] Preserve table structure: sheet name, page number, cell coordinates, row/column headers, merged cells, confidence.
- [x] Add low-confidence queue for OCR pages, tables, handwritten-looking regions, stamps/seals/signature-like regions.
- [ ] Add side-by-side page viewer: source page, extracted text, table preview, confidence badges.
- [x] Add human verification action: accept extraction, correct text, mark unreliable, re-run extraction.
- [x] Add queued long-document analysis jobs for large PDFs, OCR-heavy files, and Excel workbooks.
- [ ] Add visual-document retrieval experiment using Qwen3-VL-Reranker or ColPali-style page embeddings for scanned PDFs.
- [ ] Verification: build a document extraction benchmark with clean PDFs, scanned PDFs, tables, merged Excel cells, forms, and Nepali PDFs.
  - 2026-05-21: Document extraction page model/API/service/frontend queue added. Queued long-document analysis API/service/UI added. Full table structure preservation and visual retrieval experiments remain release gates.

## Phase 6: Model Lab, Routing, And Benchmark Harness

**Timeline:** 3-5 weeks. Start immediately after Phase 1 schema is stable.

**Outcome:** We can answer "which LLM is best?" with measured bank data.

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/services/llm_gateway.py`
- Modify: `backend/app/services/llm_service.py`
- Create: `backend/app/models/model_registry.py`
- Create: `backend/app/schemas/model_registry.py`
- Create: `backend/app/services/model_benchmark_service.py`
- Create: `backend/app/api/model_lab.py`
- Modify: `backend/app/main.py`
- Create: `backend/alembic/versions/012_model_registry_and_benchmarks.py`
- Create: `frontend/src/pages/ModelLab.jsx`
- Modify: `frontend/src/components/lipicore/ModelModeSelector.jsx`
- Modify: `frontend/src/utils/modelRoutingPreview.js`
- Modify: `tests/load/locustfile.py`
- Create: `tests/load/model_matrix.py`
- Create: `backend/tests/test_llm_gateway.py`
- Create: `backend/tests/test_model_benchmark_service.py`

- [x] Replace hard-coded fast/deep profile logic with a model registry: key, label, provider, api_base, model_name, max_context, max_output, concurrency limit, queue timeout, capabilities, enabled flag.
- [x] Add capability tags: `fast_chat`, `analyst`, `long_context`, `vision`, `embedding`, `reranker`, `structured_output`, `thinking`.
- [x] Add route policy: staff short answer -> fast; compliance strict -> analyst; loan file synthesis -> analyst/long-context; OCR image -> vision; benchmark -> requested model.
- [ ] Add priority queues: interactive staff chat over batch eval, compliance/loan workflows over background summaries.
- [x] Add model status metrics: active, waiting, queue age, p50/p95 first-token, p50/p95 full-response, tokens/sec, error rate.
- [x] Add benchmark runner for model candidates and embedding/reranker candidates.
- [ ] Add standard evaluation suites: customer care, compliance, lending, bilingual, long-document, hallucination traps, OCR extraction.
- [x] Add side-by-side model comparison UI with red/yellow/green claim readiness.
- [ ] Verification: run benchmark matrix before and after each model change; fail release if not-found or source recall regresses.
  - 2026-05-21: Runtime registry, route policy, Model Lab API/page, candidate matrix, and report summarizer added. Full priority queues and automated release gates remain.

## Phase 7: Load Handling And Concurrency

**Timeline:** 2-4 weeks after Model Lab.

**Outcome:** Load claims are measured and repeatable.

**Files:**
- Modify: `backend/app/services/llm_gateway.py`
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/api/analytics.py`
- Modify: `tests/load/locustfile.py`
- Modify: `tests/load/stream_smoke.py`
- Create: `tests/load/benchmark_prompts/customer_care.json`
- Create: `tests/load/benchmark_prompts/compliance.json`
- Create: `tests/load/benchmark_prompts/loan_support.json`
- Modify: `docs/sizing/production-tiers.md`
- Create: `docs/sizing/model-capacity-runbook.md`

- [ ] Measure 25, 50, 75, 100 active staff with real multi-user tokens.
- [ ] Separate API-only, short chat, RAG chat, queued long-document, and batch-workflow scenarios.
- [ ] Add first-token latency measurement in stream smoke.
- [ ] Add cancellation and timeout handling for queued or abandoned streams.
- [ ] Add per-bank, per-role, and per-workflow queue limits.
- [x] Add autoscaling guidance: add fast model replica when p95 first-token exceeds threshold; add deep model replica when queue timeout exceeds threshold; lower max context when KV cache pressure rises.
- [x] Update docs with measured hardware profile, exact model, quantization, context, max sequences, max batched tokens, and queue settings.
- [ ] Verification: keep HTML Locust reports and JSON summaries as release evidence.
  - 2026-05-21: Model capacity runbook added with remote L40S baseline and model-swap gates. Full 25/50/75/100 active-staff runs remain release evidence.

## Phase 8: HA/SLA Deployment Tiers

**Timeline:** 4-8 weeks, driven by bank infrastructure commitment.

**Outcome:** We can sell SLA by tier instead of making blanket availability claims.

**Files:**
- Modify: `deploy/ha/README.md`
- Modify: `deploy/ha/docker-compose.ha.example.yml`
- Create: `deploy/ha/postgres/README.md`
- Create: `deploy/ha/qdrant/README.md`
- Create: `deploy/ha/redis/README.md`
- Create: `deploy/ha/gpu-workers/README.md`
- Create: `deploy/ha/backup-restore-runbook.md`
- Create: `deploy/ha/disaster-recovery-runbook.md`
- Create: `docs/sizing/sla-tier-matrix.md`
- Modify: `deploy/upgrade.sh`

- [x] Define Pilot tier: single node, backups, no HA claim.
- [x] Define Department tier: separate workers, monitoring, backups, restore test, optional model replica.
- [x] Define Whole-bank HA tier: HA Postgres, Qdrant 3+ node cluster or managed private cluster, Redis Sentinel/Cluster, backend/frontend replicas, GPU model replicas, load balancer, alerting, backup restore drills.
- [x] Add health checks for DB, Qdrant, Redis, MinIO, backend, frontend, nginx, each model endpoint, disk, GPU memory, queue depth.
- [x] Add backup and restore scripts with quarterly restore drill instructions.
- [ ] Add blue/green or canary upgrade procedure for backend/frontend without touching user data.
- [x] Add model rollback procedure: previous weights, previous compose config, benchmark rerun.
- [ ] Verification: run failover drill, restore drill, model restart drill, and upgrade rollback drill before any SLA claim.
  - 2026-05-21: SLA tier matrix and HA runbooks added. Real failover/restore drills remain required before bank SLA claims.

## Implementation Order

1. Phase 0: clean claims and bank reply assets.
2. Phase 1: close trust foundation gaps.
3. Phase 6: add model lab because every later claim depends on measured model evidence.
4. Phase 2: customer care and branch pilot workflow.
5. Phase 3: compliance workspace.
6. Phase 4: lending decision-support workspace.
7. Phase 5: document intelligence confidence workflow.
8. Phase 7: load and concurrency evidence.
9. Phase 8: HA/SLA deployment tier.

## Minimum Bank Demo Before Next Reply

Have these working before serious bank demos:

- Strict policy mode with source-backed refusal.
- Source passage viewer with citation status.
- Document approval lifecycle and freshness fields.
- Customer-care pilot evaluation set.
- Loan support mock workflow that says "decision support only."
- Compliance circular impact demo with reviewer approval.
- Model status and queue dashboard.
- Load test evidence for the exact demo server.
- One-page SLA tier matrix.

## Definition Of Done

This roadmap is done when:

- Product copy no longer overclaims high-risk capabilities.
- Each bank-requested capability has a controlled workflow, human approval state, source trace, and audit trail.
- Each model or runtime recommendation has benchmark evidence on LipiCore workloads.
- Customer care pilot can be sold without engineering caveats beyond known limitations.
- Compliance and lending modules produce reviewable drafts, not automated decisions.
- HA/SLA claims are tied to a named deployment tier and drill evidence.
