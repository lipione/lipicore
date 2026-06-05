# LipiCore Model Lab Runbook

Use this runbook when evaluating or changing local model endpoints for LipiCore. The goal is controlled evidence: speed, quality, source discipline, clause/page citation behavior, Nepali/English behavior, OCR/image usefulness, and GPU capacity under realistic bank workloads.

Do not treat Model Lab as a reason to download or swap models casually. Run inventory first, confirm disk/GPU headroom, test one candidate at a time, and preserve the current known-good endpoint until a candidate passes.

## Step 1: Capture Runtime Inventory

Run inventory before any model change:

```bash
python tools/model_lab/remote_inventory.py \
  --host <server-host-or-ip> \
  --user <ssh-user> \
  --output reports/model-lab/remote_inventory.txt
```

The script is read-only. It records OS, CPU, memory, disk, GPU state, Docker containers/images, local model directories, and likely OpenAI-compatible `/v1/models` endpoints.

Also capture:

```bash
nvidia-smi
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep 'lipicore-vllm'
curl -s http://127.0.0.1:8002/v1/models || true
curl -s http://127.0.0.1:8003/v1/models || true
curl -s http://127.0.0.1:8007/v1/models || true
```

## Step 2: Choose A Test Lane

Use one lane per experiment:

- **Fast staff chat:** short customer-care, branch, and drafting prompts. Optimize for first-token latency and concise answers.
- **Analyst/deep:** policy, compliance, comparison, and longer reasoning prompts. Optimize for source discipline, heading/clause/page citation behavior, and lower error rate.
- **Long-document:** queued PDF/OCR/Excel analysis. Test through the queued workflow, not only synthetic long prompts.
- **Document-image:** image-heavy or page-review prompts. Keep this separate from normal OCR text extraction, which uses direct parsers and Tesseract.
- **Retrieval:** embedding or reranker experiments. Use a parallel Qdrant collection; do not mutate production embeddings in place.

## Step 3: Prepare Endpoints

Copy the example endpoint file:

```bash
cp tools/model_lab/endpoints.example.json reports/model-lab/endpoints.remote.json
```

Edit `reports/model-lab/endpoints.remote.json` with the actual endpoint URLs and served model names.

If the host does not have spare GPU memory, do not start another model. Schedule a maintenance window, pause only the approved service, benchmark the candidate, then restore the baseline if it fails.

## Step 4: Run Benchmarks

Smoke test:

```bash
python tools/model_lab/benchmark_openai.py \
  --endpoints reports/model-lab/endpoints.remote.json \
  --prompts tools/model_lab/prompts.bank-core.json \
  --output-dir reports/model-lab/smoke \
  --concurrency 1 \
  --repeat 1 \
  --max-tokens 256
```

Concurrency sweep:

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

## Step 5: Run Product Gates

Before promoting a candidate:

1. Run the bank-specific RAG evaluation gate in `/evaluations`.
2. Test not-found/refusal behavior.
3. Test English and Nepali output if the bank expects both.
4. Test one source-backed customer-care or branch prompt.
5. Test one compliance/policy prompt.
6. Verify policy-like answers include heading, clause, PDF page, printed page where available, and correct `citation_incomplete` handling when required citation fields are missing.
7. For long-document claims, queue a clean PDF, scanned PDF, Excel workbook, and bilingual/Nepali document where relevant.

## Decision Rules

Reject a candidate if:

- error rate is above 2 percent;
- p95 first-token latency misses the lane target;
- source/refusal behavior regresses;
- heading, clause, PDF page, printed page, or citation-incomplete behavior regresses for policy-like answers;
- Nepali output is corrupted or mixed-script when Nepali was requested;
- the model ignores source-required instructions;
- GPU memory leaves no operational headroom;
- licensing or airgapped packaging is not acceptable.

Promote only with saved benchmark artifacts under `reports/model-lab/<date>-<model>-<scenario>/`.

## Final Report Shape

Each model decision should include:

- hardware: GPU, VRAM, driver, disk, RAM;
- runtime: vLLM/SGLang/TensorRT-LLM version and launch flags;
- model: exact path or model ID, quantization, context length, max sequences;
- workload: prompt suite, RAG eval suite, concurrency, token caps;
- large-file workload: file types, selected excerpt metadata, job duration, source usefulness;
- results: p50/p95 first-token, p50/p95 total latency, error rate, qualitative notes;
- decision: keep, reject, or promote to pilot.
