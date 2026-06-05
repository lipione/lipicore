# LipiCore Model Capacity Runbook

Use this runbook before making any concurrency, latency, model-quality, or staff-capacity claim to a bank.

## Evidence Required

Every capacity recommendation must record:

- server CPU, RAM, disk, GPU model, VRAM, driver, and CUDA version;
- runtime: vLLM, SGLang, TensorRT-LLM, or other;
- model identifier, quantization, context length, tensor parallelism, max sequences, and max batched tokens;
- endpoint route: fast, deep, vision, or experimental;
- prompt set and version;
- concurrency, repeat count, max output tokens, temperature;
- p50/p95 first-token latency;
- p50/p95 total latency;
- error rate and timeout count;
- Redis queue depth and model admission-control state;
- qualitative notes for English, Nepali, source refusal, citation behavior, clause/page citation fidelity, and answer concision.

## Route Capacity Rule

`LLM_A`, `LLM_B`, `LLM_C`, and `LLM_VISION` are logical routes. They are not independent capacity unless they point to independent model servers with separate GPU headroom.

If multiple routes share one vLLM endpoint, size concurrency against that single endpoint. Do not add route limits together as if they were separate GPUs.

## Inventory Commands

```bash
nvidia-smi
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep 'lipicore-vllm'
curl -s http://127.0.0.1:8002/v1/models || true
curl -s http://127.0.0.1:8003/v1/models || true
curl -s http://127.0.0.1:8007/v1/models || true
docker compose logs --tail=100 backend
docker compose logs --tail=100 redis
```

Authenticated operators should also check:

```text
GET /api/chat/models/status
```

## Benchmark Lanes

| Lane | Workload | Priority |
| --- | --- | --- |
| Fast | short staff chat, customer care, branch support, drafting | first-token latency, concise output |
| Analyst | policy Q&A, compliance review, comparison | source discipline, low error rate |
| Long-document | queued PDF/OCR/Excel analysis | job duration, selected excerpt quality, worker/model queue behavior |
| Vision | image-heavy document notes and review | visual usefulness, cost, latency, clear limits |
| Evaluation | RAG gate and seed packs | source recall, not-found behavior, citation terms |
| Internal workspace | employee search, notifications, CEO messages, rates, staff inbox | API/database latency; not a model-quality benchmark unless the workflow calls a model |

## Model Swap Procedure

1. Confirm which endpoint may be paused or replaced.
2. Save `docker inspect`, `nvidia-smi`, `/v1/models`, and current `.env`/compose override evidence.
3. Start one candidate model only.
4. Run a concurrency-1 smoke benchmark.
5. Run staff benchmark at concurrency 5.
6. If stable, run 20/40/75 user tiers or the agreed target tier.
7. Run the bank-specific RAG evaluation gate.
8. Confirm policy-like answers still return required heading, clause, PDF page, and printed page when available, or `citation_incomplete` when required citation fields are missing.
9. Save JSON, CSV, and operator notes under `reports/model-lab/<date>-<model>-<scenario>/`.
10. Restore the previous endpoint and rerun smoke tests if the candidate fails.

## Release Gates

A model route is not bank-demo-ready if any of these are true:

- error rate is above 2 percent;
- p95 first-token latency exceeds the tier target;
- source-required refusal or not-found cases fail;
- Nepali output is corrupted or mixed-script when Nepali is requested;
- citation behavior regresses, including heading, clause, PDF page, and citation-incomplete handling;
- GPU memory leaves no operational headroom;
- long-document tests were synthetic only and did not use the queued workflow.

## Tier Targets

| Tier | Workload | p95 first token | p95 total | Notes |
| --- | --- | ---: | ---: | --- |
| Fast | short staff chat | under 2.5s | under 8s | Customer care and branch support. |
| Analyst | policy and compliance | under 5s | under 20s | Citation quality matters more than raw speed. |
| Long context | queued large files and comparisons | under 10s | case-specific | Use queued jobs and staff review. |
| Batch | eval and summaries | queueable | queueable | Must not starve interactive chat. |

Targets are planning thresholds. Contractual SLA language requires the deployment tier evidence in [sla-tier-matrix.md](sla-tier-matrix.md).

## Long-Document Test Scenarios

Before claiming a model is good for large-file work, test through `/api/long-document-analysis`:

- clean 100-page policy PDF;
- scanned PDF near the configured `OCR_MAX_PAGES` cap;
- Excel workbook with multiple sheets, formulas, merged ranges, and named tables;
- bilingual English/Nepali circular;
- unsupported-question prompt where selected excerpts do not contain the answer.

Record selected excerpt size, total extracted characters, p50/p95 job duration, failure rate, source usefulness, and staff correction notes.
