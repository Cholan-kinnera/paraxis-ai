# Data Architecture & Database Strategy — Paraxis AI

> **Purpose**: Database schema conventions, pgvector configuration, indexing strategies, soft deletion rules, and migration governance for Paraxis AI.

---

## 1. Database Foundation & Engine

- **Primary Database**: PostgreSQL 16
- **Extensions**:
  - `uuid-ossp`: Canonical UUID v4 primary key generation.
  - `vector`: High-performance vector embeddings and similarity indexing.
- **Connection Pooling**: PgBouncer or Django persistent connection pooling.
- **Naming Conventions**:
  - Tables: Plural snake_case (`incidents`, `campus_buildings`, `audit_logs`).
  - Columns: Lowercase snake_case (`created_at`, `building_id`, `is_active`).
  - Primary Keys: `id` (UUID v4 for domain entities, BIGSERIAL for high-throughput append-only audit logs).
  - Foreign Keys: `{singular_model}_id` (`campus_id`, `reporter_id`).

---

## 2. Multi-Tenant Partitioning Strategy

Every tenant-scoped table MUST include:
```sql
organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
campus_id UUID NOT NULL REFERENCES campuses(id) ON DELETE RESTRICT
```

### Composite Tenant Indexes
To guarantee fast lookups and strictly partitioned query execution, all high-frequency tables feature composite B-Tree indexes:
```sql
CREATE INDEX idx_incidents_tenant_status ON incidents (campus_id, status, created_at DESC);
CREATE INDEX idx_tasks_tenant_dept ON tasks (campus_id, department_id, status);
CREATE INDEX idx_assets_tenant_room ON assets (campus_id, room_id);
```

---

## 3. pgvector & Semantic Embedding Architecture

### 3.1 Vector Table Definition (`knowledge_embeddings`)
```sql
CREATE TABLE knowledge_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    campus_id UUID NOT NULL REFERENCES campuses(id),
    source_type VARCHAR(64) NOT NULL, -- 'POLICY', 'SOP', 'INCIDENT_MEMORY', 'FACILITY'
    source_id UUID,
    chunk_index INT NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(768) NOT NULL, -- Google text-embedding-004 (768-dim)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.2 Vector Indexing
We utilize the **HNSW (Hierarchical Navigable Small World)** index for sub-millisecond approximate nearest neighbor (ANN) retrieval:
```sql
CREATE INDEX idx_knowledge_embeddings_hnsw 
ON knowledge_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 3.3 Atomic Scoped Retrieval Query
Semantic retrieval joins tenant boundaries directly in SQL:
```sql
SELECT id, source_type, content, 1 - (embedding <=> :query_vector) AS cosine_similarity
FROM knowledge_embeddings
WHERE campus_id = :campus_id
  AND (source_type = :source_type OR :source_type IS NULL)
ORDER BY embedding <=> :query_vector
LIMIT :limit_k;
```

---

## 4. Soft vs. Hard Deletion Invariants

1. **Transactional Domain Entities** (`Incident`, `Task`, `Asset`, `User`):
   - **Soft deletion only**: `deleted_at TIMESTAMPTZ NULL`.
   - Deleted entities are excluded by default via Django's `ActiveManager`.
   - Never purge historical operational data permanently; needed for SLA metrics and recurring pattern analysis.
2. **Audit & Telemetry Tables** (`AuditLog`, `IncidentEvent`, `AgentRun`, `AgentToolCall`):
   - **Immutable append-only**: Deletion is prohibited at the ORM layer.
3. **Transient Cache**: Handled in Redis with explicit TTLs.

---

## 5. Migration Governance

- All migrations are managed exclusively via Django's migration engine in `backend/core`.
- Schema migrations must be backwards-compatible (expand-and-contract pattern) to support zero-downtime rolling deployments.
- No raw DDL scripts executed outside tracked migration files.
