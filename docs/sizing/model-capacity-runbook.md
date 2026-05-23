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

The 2026-05-23 post-deployment remote inventory found:

- Ubuntu 22.04.3, 16 CPU cores, 125 GiB RAM.
- 2 x NVIDIA L40S, 46 GiB each.
- `/` has about 26 GiB free and `/data` has about 584 GiB free.
- Running endpoints:
  - `lipicore-vllm-c` / `gemma-4-26b-4bit` on GPU 1, debug port `8003`.
  - `lipicore-vllm-vision` / `qwen3-vl-8b` on GPU 0, debug port `8007`.
- `lipicore-vllm-b` is not running on the current production profile.
- GPU memory is already heavily occupied, around 38.9/46 GiB on GPU 0 and 40.7/46 GiB on GPU 1 at the last check. New model tests require a controlled swap window.
- Keep the Gemma 26B text/analyst tier on GPU 1 unless explicitly testing analyst replacements.

Benchmark artifacts are under `reports/model-lab/`.

## Routing Defaults

- Current production: `ask_knowledge`, short staff drafts, customer-care responses, `approved_knowledge`, compliance review, document comparison, loan support, and queued long-document analysis all route to the Gemma 4 26B endpoint.
- Future capacity profile: short staff chat may move back to a fast tier after GPU memory and quality tests prove it is stable.
- Vision/OCR page review routes to the dedicated Qwen3-VL endpoint. Do not make strong scanned-document claims until bank-specific OCR/PDF/XLS benchmarks are recorded.

## Vision Endpoint

`docker-compose.yml` includes `vllm-vision` behind the `vision` profile so it is not started accidentally on constrained two-GPU pilots. On the current production server, `lipicore-vllm-vision` is already running. For a new server, start it only after reserving a GPU:

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
