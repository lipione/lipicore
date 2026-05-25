# LipiCore Model Lab Runbook

This runbook is for finding the best local model stack for the bank staff AI appliance. It is not a license to download every model on the internet. Run inventory first, confirm disk/GPU budget, then test a controlled matrix.

## Current Remote Access Status

From this Codex workspace:

- Public health endpoint is reachable: `https://ai.silverlining.com.np/health`.
- Remote production path is `/data/bankai`.
- The latest deployed commit is `615d299`.
- The active production model containers are `lipicore-vllm-c` and
  `lipicore-vllm-vision`.
- Do not include passwords or private keys in this file. Use the approved
  operator access path for inventory and model-swap windows.

Inventory command shape:

```bash
ssh-add /path/to/server_key
python tools/model_lab/remote_inventory.py \
  --host 202.51.2.50 \
  --port <ssh-port> \
  --user <ssh-user> \
  --output reports/model-lab/remote_inventory.txt
```

After inventory, confirm the current production vision endpoint separately on
the remote server if the inventory output does not include port `8007`:

```bash
curl -s http://127.0.0.1:8007/v1/models
```

## Step 1: Remote Inventory

Run the read-only inventory before downloading or changing model services:

```bash
python tools/model_lab/remote_inventory.py \
  --host <server-host-or-ip> \
  --user <ssh-user> \
  --output reports/model-lab/remote_inventory.txt
```

The script checks:

- OS, CPU, memory, disk.
- NVIDIA GPU state.
- Docker containers and images.
- Existing model directories under `/data/models`, `/models`, and common Hugging Face cache paths.
- OpenAI-compatible `/v1/models` endpoints on likely local model ports.

It does not stop containers, delete files, or mutate the server.

## Step 2: Select Candidate Models

Use:

```bash
tools/model_lab/model_candidate_matrix.json
```

Start with three lanes:

- Fast staff chat: no active fast endpoint on the current production profile; test Gemma 4 4B, Gemma 3 12B, or another small candidate only in a controlled swap window.
- Analyst/long-doc: current Gemma 26B baseline, Qwen3-30B-A3B 2507 or FP8 variant. Test through queued long-document jobs for realistic extraction, context-packing, and queue pressure.
- Vision/image: current Qwen3-VL 8B baseline for image-heavy analysis. OCR text extraction is handled by open-source Tesseract and should be benchmarked separately from vision prompts.
- Retrieval: BGE-M3, Jina embeddings v3, Qwen3 embedding/reranker.

Do not change embeddings in production without creating a parallel Qdrant collection or migration plan.

## Step 3: Serve One Candidate At A Time

Keep the current text and vision services as baseline. Add a candidate endpoint on a separate port, for example `8004`, only if GPU memory allows; otherwise pause one model inside a maintenance window and benchmark before replacing anything.

Example endpoint file:

```bash
cp tools/model_lab/endpoints.example.json reports/model-lab/endpoints.remote.json
```

Edit `reports/model-lab/endpoints.remote.json` to match actual reachable model endpoints.

## Step 4: Benchmark

Run a small smoke test first:

```bash
python tools/model_lab/benchmark_openai.py \
  --endpoints reports/model-lab/endpoints.remote.json \
  --prompts tools/model_lab/prompts.bank-core.json \
  --output-dir reports/model-lab/smoke \
  --concurrency 1 \
  --repeat 1 \
  --max-tokens 256
```

Then run concurrency sweeps:

```bash
python tools/model_lab/benchmark_openai.py \
  --endpoints reports/model-lab/endpoints.remote.json \
  --prompts tools/model_lab/prompts.bank-core.json \
  --output-dir reports/model-lab/concurrency-10 \
  --concurrency 10 \
  --repeat 3 \
  --max-tokens 384
```

Outputs:

- `model_benchmark_report.json`
- `model_benchmark_results.csv`

## Step 5: Decision Rules

A candidate can replace baseline only if it improves the target lane without breaking safety:

- Source/refusal behavior does not regress.
- Nepali/English answer quality is acceptable.
- p95 first-token latency stays acceptable for staff chat.
- Deep model queue does not time out under expected concurrency.
- Long-context mode is tested through realistic queued large-file jobs, not just advertised maximum context.
- License and airgapped packaging are acceptable.

## Recommended First Test Matrix

1. Current Gemma 26B text baseline at realistic staff concurrency.
2. Open-source Tesseract OCR on scanned PDF/image text extraction, plus current Qwen3-VL 8B on separate image-heavy analysis tasks.
3. Candidate fast endpoint only after freeing GPU memory.
4. Current deep vs Qwen3-30B-A3B-Instruct-2507 FP8 if GPU memory is tight.
5. Current embedding model vs BGE-M3 in a parallel retrieval collection.
6. Add Qwen3 reranker only if source recall is good but citation precision is weak.

## Final Report Shape

The final model report should include:

- Hardware: GPU, VRAM, driver, disk, RAM.
- Runtime: vLLM/SGLang/TensorRT-LLM version and launch flags.
- Model: exact path or Hugging Face ID, quantization, context, max sequences.
- Workload: prompt suite, RAG eval suite, concurrency, token caps.
- Large-file workload: clean PDF, scanned PDF, Excel workbook, bilingual circular, selected excerpt metadata, and job duration.
- Results: p50/p95 first-token, p50/p95 full latency, error rate, qualitative answer notes.
- Decision: keep, reject, or promote to pilot.
