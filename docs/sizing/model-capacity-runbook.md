# LipiCore Model Capacity Runbook

Use this runbook before making any concurrency, latency, or model-quality claim to a bank.

## Evidence Required

Every model recommendation must record:

- Server CPU, RAM, disk, GPU model, driver, CUDA version.
- Runtime: vLLM, SGLang, TensorRT-LLM, or other.
- Model identifier, quantization, context length, max model length, tensor parallelism, max sequences, max batched tokens.
- Prompt set name and version.
- Concurrency, repeat count, max output tokens, temperature.
- p50/p95 first-token latency.
- p50/p95 total latency.
- Error rate and timeout count.
- Qualitative notes for English, Nepali, source refusal, and answer concision.

## Current Remote Baseline

The 2026-05-21 remote inventory found:

- Ubuntu 22.04.3, 16 CPU cores, 125 GiB RAM.
- 2 x NVIDIA L40S, 46 GiB each.
- `/data` has about 606 GiB free.
- Initial running endpoints: Gemma fast, Gemma 26B AWQ, and Qwen2.5 7B AWQ voice.
- Qwen2.5 voice was removed from the active vLLM set during the 2026-05-21 swap window.
- Both GPUs were heavily occupied, so new model tests require a controlled swap window. Keep the Gemma 26B analyst tier on GPU 1 unless explicitly testing analyst replacements.

Benchmark artifacts are under `reports/model-lab/`.

## Routing Defaults

- `ask_knowledge`, short staff drafts, and customer-care responses route to the fast tier unless the user explicitly selects another model.
- `approved_knowledge`, compliance review, document comparison, loan support, and queued long-document analysis route to the analyst tier.
- Vision/OCR page review routes to the dedicated `vision` profile. The first implementation target is `Qwen/Qwen3-VL-8B-Instruct`; do not make scanned-document claims until it is deployed and benchmarked.

## Vision Endpoint

`docker-compose.yml` includes `vllm-vision` behind the `vision` profile so it is not started accidentally on constrained two-GPU pilots. Start it only after reserving a GPU:

```bash
docker compose --profile vision up -d vllm-vision
```

Default settings target `Qwen/Qwen3-VL-8B-Instruct` on GPU 0, port `8007`, 8192-token context, max two concurrent sequences, and persisted Hugging Face cache under `/data/models/hf_cache`. On a two-L40S host, run this instead of the small fast endpoint unless GPU memory tests prove both can safely coexist.

## Model Swap Procedure

1. Confirm which current model endpoint may be paused.
2. Capture `docker inspect`, `nvidia-smi`, and `/v1/models` output before any change.
3. Start one candidate model only.
4. Run smoke benchmark at concurrency 1.
5. Run staff benchmark at concurrency 5.
6. If stable, run 20/40/75 user load tiers with real RAG prompts.
7. Save JSON, CSV, and operator notes under `reports/model-lab/<date>-<model>-<scenario>/`.
8. Restore the previous endpoint and rerun smoke tests if the candidate fails.

## Release Gates

A model is not bank-demo-ready if any of these are true:

- Error rate is above 2 percent.
- p95 first-token latency exceeds the tier target.
- It fails not-found/refusal cases.
- Nepali output is corrupted or mixed-script for staff-facing use.
- It cannot cite or follow source-backed instructions reliably.
- It requires GPU memory that leaves no operational headroom.

## Tier Targets

| Tier | Workload | p95 first token | p95 total | Notes |
| --- | --- | ---: | ---: | --- |
| Fast | short staff chat | under 2.5s | under 8s | Customer care and branch support |
| Analyst | policy and compliance | under 5s | under 20s | Citation quality matters more than raw speed |
| Long context | queued large files and comparisons | under 10s | case-specific | Must use queued jobs, selective excerpt packing, and staff review |
| Batch | eval and summaries | queueable | queueable | Must not starve interactive staff chat |

## Long-Document Test Scenarios

Before claiming a model is good for large-file work, benchmark it through the queued workflow, not only with a synthetic long prompt.

Minimum scenarios:

- Clean 100-page policy PDF.
- Scanned PDF near the configured `OCR_MAX_PAGES` cap.
- Excel workbook with multiple sheets, formulas, merged ranges, and named tables.
- Bilingual English/Nepali circular.
- Unsupported-question prompt where the selected excerpts do not contain the answer.

Record selected excerpt size, total extracted characters, p50/p95 job duration, failure rate, source usefulness, and staff correction notes.
