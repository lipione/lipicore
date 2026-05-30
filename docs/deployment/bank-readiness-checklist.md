# Bank Readiness Checklist

Use this checklist before calling a LipiCore deployment bank-ready.

## Required Evidence

- TLS enabled for every staff-facing route.
- Strong `.env` secrets set outside git.
- PostgreSQL backup completed within the last 24 hours.
- PostgreSQL restore drill completed within the last 30 days.
- MinIO/object storage backup completed within the last 24 hours.
- Qdrant snapshot completed within the last 7 days.
- Redis persistence or accepted queue-loss policy documented.
- Model health endpoint checked after deployment.
- RAG evaluation gate passed on the bank's approved documents.
- Representative upload test completed for PDF, scanned PDF, DOCX, XLSX, PPTX, TXT/CSV, and image.
- Queue depth and GPU utilization reviewed.
- Rollback command tested in staging or documented for the release.

## Blockers

- No TLS.
- No restore drill.
- No approved-document evaluation run.
- Failed model health.
- Failed backup.
- Unknown admin access owner.
- Any cross-bank or cross-session data leak.
