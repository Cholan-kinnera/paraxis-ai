# ADR-003: PostgreSQL with pgvector for Unified Relational and Vector Storage

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Paraxis AI requires persistent storage for relational entities (Organizations, Campuses, Incidents, Tasks, SLAs, Audit Logs) as well as vector embeddings for operational RAG (campus policies, standard operating procedures, historical incident memory, and duplicate detection).

## Problem
Introducing a dedicated standalone vector database (such as Pinecone, Qdrant, Milvus, or Weaviate) introduces:
- A secondary data store to manage, backup, and monitor.
- Dual-write consistency problems between relational incident records and vector embeddings.
- Increased operational complexity and infrastructure cost.
- Friction in local development environments.

## Decision
Use **PostgreSQL 16 with the `pgvector` extension** as the single unified data store for both relational data and vector embeddings.
- Relational tables are managed via Django ORM.
- Vector tables (e.g., `knowledge_documents`, `incident_embeddings`) store high-dimensional embeddings (e.g., 768-dim from Google Gemini / text-embedding-004 or 1536-dim from OpenAI) indexed using HNSW (Hierarchical Navigable Small World) or IVFFlat.
- Tenancy filtering (`organization_id`, `campus_id`) is joined natively in SQL, guaranteeing atomic tenant isolation during semantic search.

## Alternatives Considered
1. **External SaaS Vector DB (Pinecone / Weaviate Cloud)**:
   - *Rejected*: Violates cloud-agnostic principle, creates external network latency, complicates offline testing and local dev.
2. **Dedicated Self-Hosted Vector DB (Qdrant / Milvus)**:
   - *Rejected*: Premature optimization; adds extra container and operational maintenance overhead.

## Consequences
- **Positive**:
  - ACID transactions across relational metadata and vector embeddings.
  - Native JOINs between vector similarity scores and operational entities (e.g., filter similar incidents within the same campus or building in a single query).
  - Minimal local footprint: single Docker container (`pgvector/pgvector:pg16`).
- **Negative**:
  - Extremely high scale (100M+ vectors) requires specialized indexing tuning, though standard campus scale (millions of records) is comfortably supported.

## Security Implications
All vector queries are protected by the same relational row-level security or query-level tenant filters as standard business data.
