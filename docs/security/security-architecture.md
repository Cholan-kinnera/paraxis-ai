# Security Architecture — Paraxis AI

> **Purpose**: Defense-in-depth security model, architectural boundaries, cryptographic controls, and platform trust invariants.

---

## 1. Defense-in-Depth Architecture

```mermaid
flowchart TD
    subgraph Layer1["Layer 1: Perimeter & Transport"]
        TLS["TLS 1.3 / HTTPS Only"]
        WAF["WAF & Rate Limiting (10 req/min/IP for reports)"]
    end

    subgraph Layer2["Layer 2: Identity & Multi-Tenancy"]
        JWT["Cryptographic JWT Authentication"]
        TenantContext["Mandatory Tenant Scoping (Org + Campus)"]
        RBAC["Least-Privilege RBAC & ABAC Gating"]
    end

    subgraph Layer3["Layer 3: AI Safety & Policy Engine"]
        Quarantine["Untrusted Input Quarantining (Prompt Injection Defense)"]
        TypedTools["Typed Tool Schemas (No Shell, No Raw SQL)"]
        PolicyGate["Deterministic Policy Engine (ALLOW / DENY / APPROVAL)"]
    end

    subgraph Layer4["Layer 4: Data Isolation & Storage"]
        RLS["Database Tenant Discriminators & Soft Deletion"]
        EncryptedSafety["Encrypted SafetyCase Domain (Restricted Officers)"]
        ImmutableAudit["Append-Only Cryptographic Audit Logging"]
    end

    TLS --> JWT
    WAF --> TenantContext
    TenantContext --> RBAC
    RBAC --> Quarantine
    Quarantine --> TypedTools
    TypedTools --> PolicyGate
    PolicyGate --> RLS
    PolicyGate --> EncryptedSafety
    RLS --> ImmutableAudit
```

---

## 2. Core Security Invariants

1. **Untrusted User Input**: All text submitted by students, staff, or ingested from external sources is untrusted. It is never concatenated directly into prompt system instructions.
2. **Untrusted AI Output**: All LLM completions are treated as untrusted suggestions until parsed through Pydantic validators and verified by the Policy Engine.
3. **No Direct Production Database Writes from FastAPI**: The intelligence platform communicates with Django Core via authenticated internal service APIs with HMAC signatures and request correlation tokens.
4. **Tenant Isolation Invariant**: No query may execute against multi-tenant tables without explicit `campus_id` filtering.
