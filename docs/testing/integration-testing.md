# Integration Testing — Paraxis AI

> **Purpose**: Guidelines for testing multi-service interactions, PostgreSQL database queries, pgvector similarity matching, and Redis pub/sub flows.

---

## 1. Scope & Execution

Integration tests in `tests/integration/` verify:
1. **Django Core & PostgreSQL**:
   - Model migrations apply cleanly.
   - Tenant scoping manager blocks cross-tenant reads.
   - Transactional rollbacks preserve audit integrity.
2. **FastAPI & pgvector**:
   - High-dimensional vector cosine distance queries execute within index constraints.
   - Combined SQL `WHERE campus_id = ...` and vector queries return strictly isolated results.
3. **Redis Pub/Sub & Telemetry**:
   - Publishing an event on `campus:events` arrives at subscribed SSE listeners.

---

## 2. Test Environment Setup
- Runs against the local `docker-compose.yml` services (`postgres` and `redis`).
- Test databases are automatically provisioned with clean schemas and destroyed after the test run.
