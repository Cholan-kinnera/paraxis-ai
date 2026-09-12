# ADR-002: Django Core Platform vs. FastAPI Intelligence Boundary

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Paraxis AI requires robust relational business modeling, strict access control, multi-tenant isolation, and auditable domain workflows. Simultaneously, it requires dynamic AI reasoning, asynchronous agent orchestration (LangGraph), vector embeddings, and streaming responses.

## Problem
Allowing an AI agent or an asynchronous intelligence framework to directly execute arbitrary ORM writes or bypass domain rules corrupts canonical business state, introduces subtle race conditions, bypasses audit trails, and elevates LLM hallucinations to source-of-truth status.

## Decision
Establish a **strict, non-negotiable architectural boundary**:
1. **Django Core (`backend/core`)**:
   - Sole owner of canonical domain state, relational database schema, tenancy, user authentication, RBAC, SLA calculation, audit records, and transactional integrity.
   - Commits all persistent business state.
2. **FastAPI Intelligence (`backend/intelligence`)**:
   - Owner of agent workflows, LangGraph graphs, model routing, operational RAG, semantic retrieval, and tool orchestration.
   - Operates as a stateless intelligence layer.
   - **Never writes directly to PostgreSQL domain tables**. All state modifications must be requested through Django's internal domain APIs (`/internal/v1/`) with mutual service authentication.
3. **The Sovereign Invariant**:
   - The LLM *proposes*.
   - The domain layer *validates*.
   - The policy engine *authorizes*.
   - The system *executes*.

## Alternatives Considered
1. **Full-stack Django (Agents inside Celery/Django Channels)**:
   - *Rejected*: Clunky asynchronous execution, awkward integration with modern LangGraph/LangChain state graphs, poor async streaming primitives.
2. **Full-stack FastAPI (FastAPI with SQLAlchemy/SQLModel for all business logic)**:
   - *Rejected*: Re-inventing battle-tested Django auth, permission systems, admin panels, complex relational migrations, and tenancy middleware under tight hackathon and enterprise timelines.

## Consequences
- **Positive**:
  - Eliminates hallucinated database corruption.
  - Audit logs and business invariants remain ironclad in Django.
  - FastAPI is free to iterate rapidly on agent graphs, prompts, and tool abstractions.
- **Negative**:
  - Requires defining internal HTTP/gRPC contracts between FastAPI and Django.
  - Adds minor network hop latency for tool execution (mitigated by local network bridge).

## Security Implications
Prevents prompt injection attacks from directly escalating into database writes or unauthorized data disclosures. Internal API communication is guarded by a shared internal service secret and network isolation.

## Operational Implications
Both Django and FastAPI run as independent processes in development and containers in production, with independent scaling characteristics.
