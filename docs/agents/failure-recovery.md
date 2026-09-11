# Failure Recovery & Resilience — Paraxis AI

> **Purpose**: Fault tolerance, circuit breakers, fallback triage, and graph execution recovery in Paraxis AI.

---

## 1. Agent Graph Failure Modes & Circuit Breakers

| Failure Scenario | Detection Mechanism | Recovery / Fallback Behavior |
| :--- | :--- | :--- |
| **LLM Provider Outage** | 3 consecutive HTTP 5xx or timeout errors from AI gateway. | **Circuit Breaker trips**: Fall back to rule-based keyword triage; mark incident as `TRIAGED_FALLBACK`; queue for background AI re-evaluation. |
| **Invalid JSON Schema** | Pydantic validation error parsing model completion. | **Self-Correction Prompt (Max 2 retries)**: Model is fed the exact validation error to reformat; on 2nd failure, fallback to raw text assignment to default campus dispatcher. |
| **Ambiguous Room / Asset** | Confidence < 0.60 when matching extracted room against campus graph. | **Clarification Flow**: Agent flags incident as `NEEDS_CLARIFICATION` and enqueues a quick clarification prompt to the reporter's UI. |
| **Tool Execution Error** | Django Core internal API returns 500 or network failure. | **Exponential Retry (3 attempts)**: If still failing, mark `AgentRun` as `FAILED`, log stack trace in `AuditLog`, and notify on-call operator. |
| **Stalled Approval** | Human approval pending for > 24 hours. | **Escalation Trigger**: Enqueue automated reminder to secondary approver or operations director. |

---

## 2. Checkpoint Resume Protocol

Because LangGraph checkpoints state at every node boundary:
- If a server worker crashes during tool execution, a new worker reloads the state from the last committed node checkpoint and safely resumes.
- Idempotency keys on all Core API calls guarantee that restarting a failed node does not produce duplicate work orders or multiple notifications.
