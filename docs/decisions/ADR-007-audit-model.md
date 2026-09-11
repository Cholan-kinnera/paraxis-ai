# ADR-007: Immutable Operational and Agent Execution Audit Trail

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Paraxis AI automates real-world campus operations, coordinates physical dispatches, and handles sensitive incidents. Campus leadership, legal compliance, and safety boards require comprehensive auditability of all actions taken by humans and AI agents.

## Problem
Standard application logs are ephemeral, lack structured relational context, and can be tampered with or deleted during log rotation. Furthermore, debugging agent decisions requires reconstructing the exact context, tool inputs, policy outputs, and human approvals that led to a specific operational outcome.

## Decision
1. **Dedicated Relational Audit Models**:
   - `AuditLog`: Captures every human or service entity mutation (CREATE, UPDATE, DELETE, APPROVE, REJECT) with timestamp, actor_id, IP, action, entity_type, entity_id, pre-mutation state, post-mutation state, and reason.
   - `AgentRun`: Captures every LangGraph execution session, linking user query, model used, latency, token consumption, and final operational plan.
   - `AgentToolCall`: Records each tool invocation initiated by an agent, storing exact parameters, policy engine evaluation result (`ALLOW`, `DENY`, `REQUIRE_HUMAN_APPROVAL`), tool output, and execution status.
2. **Immutability Invariant**:
   - Audit records are append-only. No UPDATE or DELETE operations are permitted on audit tables at the application or ORM level.

## Alternatives Considered
1. **Plain Text / Stdout Log Files (ELK/Loki only)**:
   - *Rejected*: Inadequate for querying historical audit histories directly within the administrative UI for compliance audits.
2. **Event Sourcing for the Entire System**:
   - *Rejected*: Extreme complexity overhead for a hackathon and early-stage startup; high barrier for team productivity.

## Consequences
- **Positive**:
  - Unquestionable accountability for both human staff and autonomous agents.
  - Granular replayability and debugging of AI agent runs.
- **Negative**:
  - Audit table storage grows steadily; requires long-term partition strategies (e.g., PostgreSQL table partitioning by year/month).

## Security Implications
Prevents repudiation of actions by actors and provides evidence if an account is compromised or an agent acts unexpectedly.
