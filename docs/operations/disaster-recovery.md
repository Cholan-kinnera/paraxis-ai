# Disaster Recovery & Business Continuity — Paraxis AI

> **Purpose**: Backup schedules, Recovery Point Objective (RPO), Recovery Time Objective (RTO), and failover procedures.

---

## 1. RTO & RPO Targets

| Tier | Service / Data Store | RPO (Max Data Loss) | RTO (Max Recovery Time) |
| :--- | :--- | :--- | :--- |
| **Tier 1** | PostgreSQL Relational Database (Incidents, Tasks, Audit) | < 5 Minutes (Continuous WAL archiving) | < 30 Minutes |
| **Tier 2** | pgvector Embeddings & RAG Knowledge Documents | < 24 Hours (Daily Snapshot) | < 1 Hour |
| **Tier 3** | Redis Transient State & Pub/Sub | N/A (Transient; rebuilt from Postgres) | < 5 Minutes |

---

## 2. Backup & Restore Procedures

1. **Daily Automated Snapshots**: Full automated PostgreSQL snapshot executed at 02:00 UTC with 30-day retention in geo-replicated object storage.
2. **Point-in-Time Recovery (PITR)**: Write-Ahead Logs (WAL) streamed continuously to enable restoration to any second within the retention window.
3. **Restoration Drill**: Quarterly automated restoration drills test restoring production backups to an isolated verification environment.
