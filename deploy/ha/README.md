# BankAi HA Deployment Profile

This is the production direction for whole-bank deployments. It is not a magic HA switch for a single server. If Postgres, Redis, Qdrant, MinIO, nginx, and both GPUs live on one machine, the deployment is not highly available.

## Required Architecture

- Load balancer or enterprise reverse proxy in front of at least two backend hosts.
- Multiple `backend` containers with `WEB_CONCURRENCY` sized per host.
- Separate `ingestion-worker` pool with queue-depth alerts.
- HA Postgres or managed Postgres with tested backup restore.
- Redis HA/Sentinel/cluster or managed Redis.
- Qdrant snapshot/replication plan, or managed vector database with bank-approved residency.
- Shared object storage for uploaded files.
- Model serving replicas sized separately for fast and deep models.

## Minimum Whole-Bank Gates

- 100 active-staff load test retained as evidence.
- Document ingestion stress test with 20 concurrent uploads.
- Backup restore test for Postgres and document storage.
- Qdrant restore or reindex runbook tested.
- Redis queue failure and worker restart tested.
- GPU failure behavior documented.

## Example Override

Use `docker-compose.ha.example.yml` as a reference for scaling API and worker containers. It assumes external data services are configured through `.env` and should be adapted by bank IT before production.

```bash
docker compose -f ../../docker-compose.yml -f docker-compose.ha.example.yml config
```
