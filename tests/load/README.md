# BankAi Load Tests

These Locust scenarios measure staff-facing capacity for normal navigation plus low-frequency LLM chat. They are intended to produce evidence for 25, 50, and 100 active-staff claims.

## Setup

```bash
python3 -m venv .venv-load
. .venv-load/bin/activate
pip install -r tests/load/requirements.txt
```

Set test credentials as environment variables. Do not hardcode real passwords in this repo.

```bash
export BANKAI_EMAIL="admin@example.com"
export BANKAI_PASSWORD="replace-me"
```

For app-capacity tests, prefer a pre-issued bearer token so the run does not become a login-rate-limit test:

```bash
export BANKAI_TOKEN="replace-me"
```

For multi-user LLM capacity tests, provide multiple comma-separated tokens. This avoids accidentally measuring the per-user LLM concurrency guard instead of whole-bank capacity:

```bash
export BANKAI_TOKENS="token-for-user-1,token-for-user-2,token-for-user-3"
```

## Run Scenarios

```bash
locust -f tests/load/locustfile.py --host https://ai.silverlining.com.np --headless --users 25 --spawn-rate 5 --run-time 10m --html reports/load-25.html --scenario-note "25 active staff"
locust -f tests/load/locustfile.py --host https://ai.silverlining.com.np --headless --users 50 --spawn-rate 5 --run-time 10m --html reports/load-50.html --scenario-note "50 active staff"
locust -f tests/load/locustfile.py --host https://ai.silverlining.com.np --headless --users 100 --spawn-rate 10 --run-time 10m --html reports/load-100.html --scenario-note "100 active staff"
```

To measure normal app/API capacity without LLM stream pressure:

```bash
BANKAI_DISABLE_STREAM=1 locust -f tests/load/locustfile.py --host https://ai.silverlining.com.np --headless --users 100 --spawn-rate 10 --run-time 10m --html reports/load-100-api.html
```

## What This Measures

- Login and token issuance under load.
- Health, session, document, and task-template API latency.
- Streamed general chat pressure against the LLM gateway.
- Basic backend worker saturation and queue behavior.

## Stream-Only Smoke

Run this inside the backend container or any environment that can import the backend app:

```bash
BANKAI_STREAM_CONCURRENCY=20 BANKAI_LOAD_CLEANUP=1 python tests/load/stream_smoke.py
```

This creates one disposable staff user per concurrent stream, issues short-lived tokens, measures the streaming path, then disables the users and removes generated chat data.

## Current Test-Server Baseline

Latest measured results on the remote test server:

- 100 active staff API-only smoke with `BANKAI_DISABLE_STREAM=1`: 2,357 requests, 0 failures, aggregate p95 57 ms.
- 20 separate staff stream smoke: 20/20 real answers, p50 8.41 s, p95 29.95 s, max 35.75 s.
- 40 separate staff stream smoke after stale queue pruning: 40/40 real answers, p50 30.61 s, p95 80.19 s, max 86.76 s.
- A single user running many concurrent streams will hit `LLM_USER_MAX_CONCURRENCY=1`; that is an abuse-control test, not a bank-capacity test.

## Pass Criteria For Product Claims

- p95 non-LLM API latency below 500 ms during 25 and 50 user runs.
- p95 streamed chat first-response latency below 10 seconds during 25 user runs.
- Error rate below 1% excluding intentional rate-limit responses.
- Redis/model queue timeouts below 1% of chat requests.
- No backend worker restarts, OOM kills, or database connection exhaustion.
- For 40+ simultaneous streaming users, report full-response p50/p95/max separately from API latency; do not hide slow tail latency inside aggregate API numbers.
