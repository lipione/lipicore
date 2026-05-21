# Backup And Restore Runbook

Run this before any formal production acceptance.

## Scope

- PostgreSQL database.
- Uploaded document object storage.
- Qdrant snapshots or reindex procedure.
- Redis/RQ queue recovery.
- Model configuration and weights manifest.

## Restore Drill

1. Record application version, migration head, model registry, and runtime configuration.
2. Take a fresh Postgres backup.
3. Take or verify object-storage backup.
4. Take Qdrant snapshot or confirm source documents can fully reindex.
5. Restore into a clean staging environment.
6. Run migrations.
7. Run health checks.
8. Open a known document, chat session, audit log, and model status page.
9. Run one approved-knowledge query with expected citation.
10. Record elapsed time and failures.

## Acceptance

The restore drill passes only if data, source citations, audit logs, users, and document metadata are available in the restored environment.
