# Capacity And Safety Baseline Plan

## Goal

Turn the vague capacity claims into measurable engineering controls: backend worker sizing, explicit upload limits, AI Task context protection, repeatable load tests, and production sizing tiers.

## Scope

1. Add backend worker configuration through `WEB_CONCURRENCY`.
2. Add explicit Document Library upload size enforcement.
3. Prevent AI Tasks from sending unbounded extracted text into the LLM context.
4. Add Locust scenarios for 25, 50, and 100 active-staff testing.
5. Document realistic pilot, department, and whole-bank sizing tiers.

## Out Of Scope For This Slice

- Celery/RQ ingestion workers.
- Reranking.
- Citation verifier.
- Full OCR and table extraction.
- Chunk-level permissions.
- HA database/vector-store deployment.

Those require deeper data-model and infrastructure changes and should be built as the next slices.
