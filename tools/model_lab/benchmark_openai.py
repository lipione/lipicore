#!/usr/bin/env python3
"""Benchmark OpenAI-compatible local model endpoints.

This is intentionally provider-neutral: vLLM, SGLang, TensorRT-LLM, and many
other runtimes can expose the same `/v1/chat/completions` shape.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable, Iterator

import httpx


DEFAULT_PROMPTS = [
    {
        "id": "staff_short_policy",
        "prompt": "In two bullet points, explain what staff should do when an approved source does not answer a bank policy question.",
    },
    {
        "id": "bilingual_nepali",
        "prompt": "Translate this staff instruction into Nepali: Please verify the customer identity before discussing account information.",
    },
    {
        "id": "long_doc_summary",
        "prompt": "Summarize the following internal circular in five concise bullet points and include open questions for staff review.\n\n"
        + ("Section 1: Staff must follow approved procedures. Section 2: Exceptions require supervisor approval. " * 80),
    },
]


def parse_sse_events(lines: Iterable[str]) -> Iterator[dict[str, Any]]:
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("data: "):
            continue
        data = line[6:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            yield json.loads(data)
        except json.JSONDecodeError:
            continue


def extract_delta_text(event: dict[str, Any]) -> str:
    choices = event.get("choices") or []
    if not choices:
        return ""
    choice = choices[0] or {}
    delta = choice.get("delta") or {}
    if "content" in delta:
        return delta.get("content") or ""
    message = choice.get("message") or {}
    return message.get("content") or ""


def percentile(values: list[float], quantile: float) -> float | None:
    cleaned = sorted(float(value) for value in values if value is not None)
    if not cleaned:
        return None
    index = min(len(cleaned) - 1, math.ceil(quantile * len(cleaned)))
    return cleaned[index]


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    successes = [result for result in results if result.get("ok")]
    failures = total - len(successes)
    first_token = [result["first_token_latency_ms"] for result in successes if result.get("first_token_latency_ms") is not None]
    total_latency = [result["total_latency_ms"] for result in successes if result.get("total_latency_ms") is not None]
    throughput = [
        (float(result.get("output_chars") or 0) / max(float(result.get("total_latency_ms") or 1) / 1000, 0.001))
        for result in successes
    ]
    return {
        "total_requests": total,
        "successful_requests": len(successes),
        "failed_requests": failures,
        "error_rate": round(failures / total, 4) if total else 0,
        "p50_first_token_latency_ms": percentile(first_token, 0.50),
        "p95_first_token_latency_ms": percentile(first_token, 0.95),
        "p50_total_latency_ms": percentile(total_latency, 0.50),
        "p95_total_latency_ms": percentile(total_latency, 0.95),
        "chars_per_second_avg": round(sum(throughput) / len(throughput), 2) if throughput else 0,
    }


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def load_prompts(path: str | Path | None) -> list[dict[str, str]]:
    if not path:
        return DEFAULT_PROMPTS
    payload = load_json(path)
    if isinstance(payload, dict):
        return payload.get("prompts") or payload.get("cases") or []
    return payload


def benchmark_one(
    *,
    endpoint: dict[str, Any],
    prompt: dict[str, str],
    timeout_seconds: float,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    url = endpoint["api_base"].rstrip("/") + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {endpoint.get('api_key', 'no-key')}"}
    model_name = endpoint.get("model") or endpoint["key"]
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt["prompt"]}],
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    started = time.perf_counter()
    first_token_at = None
    output_parts: list[str] = []
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                for event in parse_sse_events(response.iter_lines()):
                    delta = extract_delta_text(event)
                    if delta and first_token_at is None:
                        first_token_at = time.perf_counter()
                    if delta:
                        output_parts.append(delta)
    except Exception as exc:
        ended = time.perf_counter()
        return {
            "model_key": endpoint["key"],
            "model": model_name,
            "prompt_id": prompt["id"],
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "total_latency_ms": round((ended - started) * 1000, 2),
        }

    ended = time.perf_counter()
    output = "".join(output_parts)
    return {
        "model_key": endpoint["key"],
        "model": model_name,
        "prompt_id": prompt["id"],
        "ok": True,
        "first_token_latency_ms": round((first_token_at - started) * 1000, 2) if first_token_at else None,
        "total_latency_ms": round((ended - started) * 1000, 2),
        "output_chars": len(output),
        "output_preview": output[:500],
    }


def run_benchmark(
    *,
    endpoints: list[dict[str, Any]],
    prompts: list[dict[str, str]],
    concurrency: int,
    repeat: int,
    timeout_seconds: float,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    jobs = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        for endpoint in endpoints:
            for prompt in prompts:
                for _ in range(max(1, repeat)):
                    jobs.append(executor.submit(
                        benchmark_one,
                        endpoint=endpoint,
                        prompt=prompt,
                        timeout_seconds=timeout_seconds,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    ))
        results = [future.result() for future in as_completed(jobs)]
    return {
        "summary": summarize_results(results),
        "results": sorted(results, key=lambda item: (item["model_key"], item["prompt_id"], item.get("total_latency_ms") or 0)),
    }


def write_outputs(report: dict[str, Any], output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "model_benchmark_report.json").write_text(json.dumps(report, indent=2))
    with (out / "model_benchmark_results.csv").open("w", newline="") as handle:
        fields = ["model_key", "model", "prompt_id", "ok", "first_token_latency_ms", "total_latency_ms", "output_chars", "error"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report["results"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark OpenAI-compatible model endpoints.")
    parser.add_argument("--endpoints", required=True, help="JSON file with an endpoints array.")
    parser.add_argument("--prompts", help="Optional JSON prompt/case file.")
    parser.add_argument("--output-dir", default="reports/model-lab")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=float, default=120)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    endpoint_payload = load_json(args.endpoints)
    endpoints = endpoint_payload.get("endpoints", endpoint_payload)
    report = run_benchmark(
        endpoints=endpoints,
        prompts=load_prompts(args.prompts),
        concurrency=args.concurrency,
        repeat=args.repeat,
        timeout_seconds=args.timeout_seconds,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    write_outputs(report, args.output_dir)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
