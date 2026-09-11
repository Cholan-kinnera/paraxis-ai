# Tenant Isolation Specification — Paraxis AI

> **Purpose**: Technical architecture guaranteeing strict multi-tenant data segregation across database queries, vector searches, and API endpoints.

---

## 1. Multi-Tenant Identity Invariant

In Paraxis AI, tenant scope is strictly hierarchical:
```
Organization (e.g., State University System)
  └── Campus (e.g., Engineering Campus, Medical Campus)
        └── Operational Records (Incidents, Tasks, Assets, Users)
```

- **Authentication Token as Single Source of Truth**: The active `tenant_id` (`campus_id`) is encoded directly in the cryptographically signed JWT issued by Django Core.
- **Payload Ignored**: Client query parameters (`?campus_id=...`) or body fields claiming tenant identity are explicitly rejected for authorization purposes.

---

## 2. Enforcement Mechanisms

### 2.1 Django ORM Tenant Manager
All multi-tenant models inherit from `TenantScopedModel`:
```python
class TenantScopedManager(models.Manager):
    def get_queryset(self):
        # Automatically scopes all queries to the campus in thread-local request context
        current_campus_id = get_current_campus_id()
        if not current_campus_id:
            raise SecurityException("No active campus context in request thread")
        return super().get_queryset().filter(campus_id=current_campus_id)
```

### 2.2 pgvector Semantic Query Isolation
All vector similarity searches against `knowledge_embeddings` MUST include a hard SQL filter on `campus_id` alongside the cosine distance operator `<=>`. Vector retrieval across tenant boundaries is mathematically impossible.

### 2.3 Automated Cross-Tenant Leakage Testing
Integration tests in `tests/integration/test_tenant_isolation.py` generate data in `Campus A` and verify that authenticated requests from `Campus B` return HTTP 404 for all entity IDs.
