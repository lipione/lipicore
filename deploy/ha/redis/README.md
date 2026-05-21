# Redis HA Notes

Redis is used for queues and model admission control. A single Redis instance is acceptable for pilot only.

Department and whole-bank deployments need:

- Redis Sentinel, Redis Cluster, or managed Redis.
- Queue-depth monitoring.
- Stale lease cleanup.
- Worker restart procedure.
- Persistence configuration appropriate for the bank support model.
