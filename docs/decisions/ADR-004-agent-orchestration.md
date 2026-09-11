# ADR-004: Agent Orchestration via Stateful LangGraph Workflow

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Autonomous agent systems frequently fail in production when unstructured "multi-agent swarms" converse uncontrollably without strict checkpoints, deterministic state transitions, or human oversight.

## Problem
In campus operations, actions carry real-world consequences (dispatching electricians, triggering building alarms, escalating disciplinary issues). Chatty, non-deterministic agent swarms lead to infinite loops, uncontrollable token consumption, hallucinated actions, and zero traceability.

## Decision
Implement a **single orchestrated, stateful workflow using LangGraph** rather than disconnected autonomous swarms.
The workflow follows a defined state machine with specialized functional nodes:
```
OBSERVE -> UNDERSTAND -> CONTEXTUALIZE -> REASON -> PLAN -> POLICY CHECK -> [HUMAN APPROVAL IF REQUIRED] -> ACT -> MONITOR -> ESCALATE -> RESOLVE -> REMEMBER -> GENERATE INSIGHT
```
1. **Explicit State Schema (`IncidentAgentState`)**: Checkpointed at every step in Redis/PostgreSQL.
2. **Deterministic Control Flow**: Conditional edge routing handles branching (e.g., if priority > High or action is sensitive, route to `human_approval_node`).
3. **Traceable Telemetry**: Each step produces a structured event with timing, token usage, and tool inputs/outputs.

## Alternatives Considered
1. **AutoGPT / CrewAI Multi-Agent Swarms**:
   - *Rejected*: Non-deterministic message passing, difficult to audit, prone to cascading errors and hallucinated delegation loops.
2. **Hardcoded Procedural Scripts (No LLM Orchestration)**:
   - *Rejected*: Inflexible; cannot handle messy, ambiguous natural-language user reports or nuanced contextual classification.

## Consequences
- **Positive**:
  - Deterministic guarantees at critical checkpoints (policy checks and human gates).
  - Resumable workflows: long-running incidents can pause for human approval and resume seamlessly.
  - Clear visualization and debugging in LangSmith / OpenTelemetry.
- **Negative**:
  - Requires upfront design of typed state graphs and schemas.

## Security Implications
Prevents autonomous runaway tool loops. Every edge transition is constrained by graph logic.
