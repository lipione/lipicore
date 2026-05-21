# Qdrant HA Notes

For whole-bank HA, use a Qdrant cluster or managed private vector database approved by bank IT.

Minimum production requirements:

- Replication or snapshot strategy.
- Collection schema documented for each embedding model.
- Reindex runbook from approved documents.
- Recall regression tests before switching embedding models.
- Disk and segment monitoring.
