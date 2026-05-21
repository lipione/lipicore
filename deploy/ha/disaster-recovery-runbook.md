# Disaster Recovery Runbook

This runbook defines operational recovery steps. It does not create an SLA by itself.

## Incident Classes

- API/frontend failure: restart or roll forward API/frontend containers.
- Model endpoint failure: fail over to another model replica or switch route policy to the available tier.
- Database failure: promote standby or restore from backup.
- Vector store failure: restore Qdrant snapshot or reindex approved documents.
- Object storage failure: restore uploaded document bucket.
- GPU failure: disable affected model endpoint and route traffic to remaining capacity.

## Minimum Response Steps

1. Freeze deployments.
2. Capture logs, metrics, and current container state.
3. Identify failed layer.
4. Apply the layer-specific recovery path.
5. Run smoke tests: login, document list, approved-knowledge answer, audit log write, model status.
6. Document user impact and recovery time.
7. Run post-incident review before any SLA report.

## Model Rollback

1. Re-enable previous model endpoint configuration.
2. Confirm `/v1/models` returns expected model.
3. Run Model Lab smoke benchmark.
4. Run one customer-care, one compliance, and one lending prompt.
5. Keep the failed model disabled until root cause is recorded.
