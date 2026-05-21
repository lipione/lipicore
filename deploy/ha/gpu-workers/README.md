# GPU Worker HA Notes

GPU model serving must be treated as capacity infrastructure, not a single magic endpoint.

Minimum production requirements:

- Separate fast and analyst model routes.
- Health check for each `/v1/models` endpoint.
- GPU memory and utilization monitoring.
- Model rollback manifest with previous weights and container command.
- Queue and timeout thresholds per workflow.
- Benchmark rerun after model, driver, CUDA, vLLM, SGLang, or TensorRT-LLM changes.
