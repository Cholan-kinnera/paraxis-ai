# ADR-005: Typed Tool Registry and Deterministic Policy Engine

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
AI agents require tools to query context and trigger operational actions. Allowing the LLM to directly decide whether to execute an action introduces unacceptable safety, privacy, and financial risks.

## Problem
Prompt injection or subtle model misalignment can trick an agent into executing destructive actions, violating organizational policies, or exposing confidential information.

## Decision
1. **Typed Tool Contracts**:
   - All tools are explicitly registered with Pydantic input and output schemas.
   - Prohibited capabilities: Raw SQL, arbitrary shell, unrestricted HTTP, and direct filesystem writes.
2. **Deterministic Policy Engine**:
   - Gating layer sits between the agent's proposed action and physical execution:
     `Agent Proposes Action -> Policy Engine Evaluates -> ALLOW / DENY / REQUIRE_HUMAN_APPROVAL -> Execution`
   - Actions classified as **Routine & Safe** (e.g., `get_location_context`, `search_related_incidents`, `assign_routine_task`) evaluate to `ALLOW`.
   - Actions classified as **Sensitive & High-Impact** (e.g., dispatching external contractors, notifying campus-wide emergency channels, altering disciplinary records) evaluate to `REQUIRE_HUMAN_APPROVAL`.
   - Actions violating security boundaries (cross-tenant access, unauthorized role access) evaluate to `DENY`.

## Alternatives Considered
1. **Unrestricted Tool Execution with System Prompt Instructions**:
   - *Rejected*: "Please do not execute sensitive tools" in system prompts is easily bypassed via jailbreaks and indirect prompt injection.
2. **Hardcoded Approvals for Every Action**:
   - *Rejected*: Paralyzes operations with alert fatigue for trivial, routine events (e.g., fetching room details).

## Consequences
- **Positive**:
  - Ironclad safety guarantees independent of LLM compliance.
  - Transparent audit trail for all policy evaluations.
- **Negative**:
  - Requires maintaining a policy rules matrix mapped to tool actions.

## Security Implications
Prevents prompt injection from directly weaponizing tool capabilities. Even if an LLM is 100% hijacked, the Policy Engine rejects unauthorized actions deterministically.
