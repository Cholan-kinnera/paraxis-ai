# Operational Runbooks — Paraxis AI

> **Purpose**: Standard Operating Procedures (SOPs) for responding to common production failure scenarios.

---

## 1. Runbook: AI Provider Outage / High Latency
- **Symptoms**: Agent triage latency exceeds 10 seconds; error rates on LLM gateway increase.
- **Action**:
  1. Inspect AI gateway logs: `docker compose logs intelligence`.
  2. Switch active provider via environment override:
     `AI_DEFAULT_PROVIDER=openai` (or fallback provider).
  3. If all external providers are degraded, activate the **Heuristic Fallback Triage Flag**:
     `ENABLE_HEURISTIC_TRIAGE=true`
     This bypasses LLM inference and routes incidents based on direct keyword matching.

---

## 2. Runbook: High Database Connection Usage
- **Symptoms**: Django logs `OperationalError: FATAL: remaining connection slots are reserved`.
- **Action**:
  1. Inspect active connections:
     ```sql
     SELECT count(*), state FROM pg_stat_activity GROUP BY state;
     ```
  2. Check for stalled long-running queries:
     ```sql
     SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
     FROM pg_stat_activity 
     WHERE state != 'idle' ORDER BY duration DESC;
     ```
  3. Terminate stuck transactions and restart PgBouncer pool.

---

## 3. Runbook: Redis Outage / Stream Disconnection
- **Symptoms**: Command Center UI stops receiving live SSE step updates.
- **Action**:
  1. Check Redis container health: `docker compose ps redis`.
  2. If Redis restarted, restart the FastAPI SSE worker to re-establish Pub/Sub subscriptions.
  3. Web UI automatically falls back to periodic polling every 5 seconds until SSE reconnects.
