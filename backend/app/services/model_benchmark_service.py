import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MATRIX_PATH = REPO_ROOT / "tools" / "model_lab" / "model_candidate_matrix.json"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports" / "model-lab"


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(quantile * len(ordered)))
    return ordered[index]


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    successes = [result for result in results if result.get("ok")]
    failed = total - len(successes)
    first_token = [
        float(result["first_token_latency_ms"])
        for result in successes
        if result.get("first_token_latency_ms") is not None
    ]
    total_latency = [
        float(result["total_latency_ms"])
        for result in successes
        if result.get("total_latency_ms") is not None
    ]
    throughput = [
        float(result.get("output_chars") or 0) / max(float(result.get("total_latency_ms") or 1) / 1000, 0.001)
        for result in successes
    ]
    return {
        "total_requests": total,
        "successful_requests": len(successes),
        "failed_requests": failed,
        "error_rate": round(failed / total, 4) if total else 0,
        "p50_first_token_latency_ms": _percentile(first_token, 0.50),
        "p95_first_token_latency_ms": _percentile(first_token, 0.95),
        "p50_total_latency_ms": _percentile(total_latency, 0.50),
        "p95_total_latency_ms": _percentile(total_latency, 0.95),
        "chars_per_second_avg": round(sum(throughput) / len(throughput), 2) if throughput else 0,
    }


def _claim_readiness(summary: dict[str, Any]) -> str:
    if summary["failed_requests"] > 0 or summary["error_rate"] >= 0.02:
        return "red"
    if (summary.get("p95_first_token_latency_ms") or 0) > 2500:
        return "yellow"
    if (summary.get("p95_total_latency_ms") or 0) > 10000:
        return "yellow"
    return "green"


def load_candidate_matrix(path: str | Path = DEFAULT_MATRIX_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def build_candidate_snapshot(matrix: dict[str, Any]) -> dict[str, Any]:
    candidates = matrix.get("candidates", [])
    return {
        "version": matrix.get("version"),
        "policy": matrix.get("policy"),
        "total_candidates": len(candidates),
        "tier_counts": dict(Counter(candidate.get("tier", "unknown") for candidate in candidates)),
        "candidates": candidates,
    }


def summarize_benchmark_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in payload.get("results", []):
        by_model[result.get("model_key") or result.get("model") or "unknown"].append(result)

    model_summaries = {}
    for key, rows in by_model.items():
        summary = _summarize_results(rows)
        summary["claim_readiness"] = _claim_readiness(summary)
        model_summaries[key] = summary

    return {
        "report_path": str(Path(path)),
        "model_count": len(model_summaries),
        "models": model_summaries,
    }


def latest_benchmark_summary(reports_dir: str | Path = DEFAULT_REPORTS_DIR) -> dict[str, Any]:
    root = Path(reports_dir)
    reports = sorted(root.glob("*/model_benchmark_report.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not reports:
        return {"model_count": 0, "models": {}, "report_path": None}
    return summarize_benchmark_report(reports[0])
