import json

from app.services.model_benchmark_service import (
    build_candidate_snapshot,
    load_candidate_matrix,
    summarize_benchmark_report,
)


def test_candidate_snapshot_groups_models_by_tier():
    matrix = load_candidate_matrix()
    snapshot = build_candidate_snapshot(matrix)

    assert snapshot["version"]
    assert snapshot["total_candidates"] >= 8
    assert snapshot["tier_counts"]["fast_chat"] >= 1
    assert snapshot["tier_counts"]["analyst"] >= 1
    assert snapshot["tier_counts"]["embedding"] >= 1


def test_benchmark_report_summarizes_each_model(tmp_path):
    report_path = tmp_path / "model_benchmark_report.json"
    report_path.write_text(json.dumps({
        "results": [
            {
                "model_key": "fast",
                "ok": True,
                "first_token_latency_ms": 100,
                "total_latency_ms": 500,
                "output_chars": 1000,
            },
            {
                "model_key": "fast",
                "ok": False,
                "total_latency_ms": 250,
                "error": "timeout",
            },
            {
                "model_key": "deep",
                "ok": True,
                "first_token_latency_ms": 300,
                "total_latency_ms": 1200,
                "output_chars": 1200,
            },
        ]
    }))

    summary = summarize_benchmark_report(report_path)

    assert summary["model_count"] == 2
    fast = summary["models"]["fast"]
    assert fast["total_requests"] == 2
    assert fast["failed_requests"] == 1
    assert fast["claim_readiness"] == "red"
    assert summary["models"]["deep"]["p50_first_token_latency_ms"] == 300
