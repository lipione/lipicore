import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def test_stream_parser_extracts_openai_delta_chunks():
    from tools.model_lab.benchmark_openai import extract_delta_text, parse_sse_events

    lines = [
        "data: {\"choices\":[{\"delta\":{\"content\":\"Na\"}}]}",
        "",
        "data: {\"choices\":[{\"delta\":{\"content\":\"maste\"}}]}",
        "data: [DONE]",
    ]

    events = list(parse_sse_events(lines))

    assert [extract_delta_text(event) for event in events] == ["Na", "maste"]


def test_benchmark_summary_reports_latency_and_error_rate():
    from tools.model_lab.benchmark_openai import summarize_results

    summary = summarize_results([
        {
            "model_key": "fast-a",
            "ok": True,
            "first_token_latency_ms": 100,
            "total_latency_ms": 900,
            "output_chars": 900,
        },
        {
            "model_key": "fast-a",
            "ok": True,
            "first_token_latency_ms": 300,
            "total_latency_ms": 1100,
            "output_chars": 1100,
        },
        {
            "model_key": "fast-a",
            "ok": False,
            "error": "timeout",
        },
    ])

    assert summary["total_requests"] == 3
    assert summary["successful_requests"] == 2
    assert summary["failed_requests"] == 1
    assert summary["error_rate"] == 0.3333
    assert summary["p50_first_token_latency_ms"] == 300
    assert summary["p95_total_latency_ms"] == 1100
    assert summary["chars_per_second_avg"] > 0


def test_remote_inventory_script_is_read_only_and_checks_model_runtime():
    from tools.model_lab.remote_inventory import build_inventory_script

    script = build_inventory_script(model_roots=["/data/models", "/models"])

    assert "nvidia-smi" in script
    assert "docker ps" in script
    assert "/v1/models" in script
    assert "find /data/models /models" in script
    forbidden = [" rm ", " rmdir ", " docker stop", " docker rm", " kill ", " pkill ", " reboot", " shutdown"]
    assert not any(term in script for term in forbidden)


def test_model_candidate_matrix_has_required_fields():
    matrix_path = REPO_ROOT / "tools" / "model_lab" / "model_candidate_matrix.json"
    matrix = json.loads(matrix_path.read_text())

    assert matrix["version"]
    assert len(matrix["candidates"]) >= 8
    for candidate in matrix["candidates"]:
        assert candidate["key"]
        assert candidate["tier"] in {"fast_chat", "analyst", "long_context", "vision", "embedding", "reranker"}
        assert candidate["runtime_priority"]
        assert candidate["test_reason"]
        assert candidate["risk_notes"]
