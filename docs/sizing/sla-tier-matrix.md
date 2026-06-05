# LipiCore SLA Tier Matrix

LipiCore availability claims must be tied to a named deployment tier. Do not make a blanket SLA claim for every bank install.

| Tier | Architecture | Suitable For | Availability Language |
| --- | --- | --- | --- |
| Pilot | Single node, local Postgres/Qdrant/Redis/MinIO, one text model route, optional separate fast/vision routes, daily backups | 20-50 users, 30-day pilot | No HA claim. Best-effort pilot support with backup and restore process. |
| Department | Separate API, worker, data, and model services where possible; monitored backups; optional model replica | Customer care, branch support, compliance lookup for one department | Department-grade resilience. SLA depends on agreed infrastructure and support window. |
| Whole-bank HA | Multiple API/frontend replicas, HA Postgres, Qdrant cluster or managed vector DB, Redis Sentinel/Cluster, redundant object storage, model replicas, load balancer, monitoring, restore drills | Enterprise bank rollout | SLA may be contracted only after failover, restore, and model-restart drills pass. |

## Drill Evidence Required

- Postgres backup restore.
- Object storage restore.
- Qdrant snapshot restore or full reindex.
- Redis queue failover or worker restart.
- Backend/frontend rolling restart.
- Model endpoint restart and rollback.
- GPU failure behavior.
- Load test report for target active user count.

## Health Checks

Production monitoring must cover:

- API `/health`
- frontend/nginx
- Postgres connection pool
- Qdrant collection health
- Redis queue depth and stale jobs
- long-document job age, failures, and backlog
- MinIO/object storage
- each model endpoint `/v1/models`
- disk free space
- GPU memory and utilization
- ingestion worker heartbeat
- p50/p95 first-token latency
- p50/p95 total model latency

## SLA Rule

Only the Whole-bank HA tier can support a formal availability SLA. Pilot and Department tiers can have support-response commitments, but should not be sold as highly available unless the bank funds and accepts the required architecture.

Long-document analysis turnaround should be treated as a separate queue-based service target, not as the same SLA as interactive chat. It depends on OCR/page count, workbook size, worker capacity, and analyst-model queue load.

Internal workspace modules such as Employee Search, Notifications, CEO Messages, Staff Inbox, and Forex/Time/Dates should be measured as API/database workflows. Their latency and availability evidence should be tracked separately from model first-token/total-latency claims.
