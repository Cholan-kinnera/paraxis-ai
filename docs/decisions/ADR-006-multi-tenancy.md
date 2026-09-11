# ADR-006: Hierarchical Multi-Tenancy (Organization -> Campus)

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Paraxis AI is designed as an enterprise SaaS product serving educational consortiums, universities, and multi-campus university systems.

## Problem
In a multi-tenant university environment, mixing or leaking operational records between distinct campuses (e.g., medical campus vs. engineering campus) or distinct institutions violates data privacy, creates massive confusion during physical dispatch, and breaches confidentiality.

## Decision
1. **Hierarchical Multi-Tenant Data Model**:
   - `Organization` (e.g., University System / Trust)
     - `Campus` (e.g., North Campus, Downtown Campus)
       - `Operational Data` (Users, Departments, Buildings, Rooms, Assets, Incidents, Tasks, Safety Cases)
2. **Tenant Resolution Invariant**:
   - Tenant context (`organization_id`, `campus_id`) is extracted strictly from cryptographically verified JWT tokens.
   - Client-provided tenant query parameters or payload attributes are explicitly ignored for authorization.
3. **Database-Level Isolation**:
   - Shared database, shared schema with mandatory tenant discriminator columns on every tenant-scoped table.
   - Custom Django ORM Base Manager automatically enforces `.filter(campus=current_campus)` on all querysets.

## Alternatives Considered
1. **Database-per-Tenant**:
   - *Rejected*: Massive operational complexity, high connection pooling overhead, unmanageable migrations across hundreds of prospective campuses.
2. **Schema-per-Tenant**:
   - *Rejected*: Adds significant migration latency and complicates cross-campus administrative reporting for institutional leadership.

## Consequences
- **Positive**:
  - Cost-effective resource utilization on standard infrastructure.
  - Clean separation of organizational governance vs. campus-level day-to-day operations.
- **Negative**:
  - Requires continuous regression testing to ensure developers never write unscoped raw queries.

## Security Implications
Guarantees tenant isolation across both relational tables and pgvector similarity searches.
