# Performance & Load Testing — Paraxis AI

> **Purpose**: Latency budgets, concurrent load targets, and stress testing protocols for Paraxis AI.

---

## 1. Latency Budgets & SLA Targets

| Operation | 95th Percentile Target (p95) | Maximum Budget |
| :--- | :--- | :--- |
| **Incident Ingestion (`POST /api/v1/incidents`)** | < 150ms | 300ms |
| **Agent Triage & Graph Execution (End-to-End)** | < 3.5s | 5.0s |
| **pgvector Cosine Search (100k vectors)** | < 15ms | 50ms |
| **SSE Event Delivery Latency** | < 200ms | 500ms |
| **Command Center Dashboard Initial Load** | < 600ms | 1.2s |

---

## 2. Load Testing Scenarios (Locust / k6)

- **Scenario 1: Campus Rush Hour**: 500 concurrent students submitting reports simultaneously after a campus-wide power surge. System must queue requests without dropping connections or dropping audit logs.
- **Scenario 2: Realtime Fanout**: 100 operations staff listening to the same campus SSE feed while 20 incidents per minute are triaged.
