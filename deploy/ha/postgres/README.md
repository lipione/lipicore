# PostgreSQL HA Notes

Use managed private Postgres or streaming replication with a documented failover path.

Minimum production requirements:

- Automated backups with retention agreed by the bank.
- Point-in-time recovery where available.
- Restore drill before go-live.
- Separate credentials for application and migration roles.
- Monitoring for connection saturation, replication lag, disk, and backup failures.
