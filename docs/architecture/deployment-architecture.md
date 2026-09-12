# Deployment Architecture — Paraxis AI

> **Purpose**: Infrastructure topology, local containerization, staging/production hosting models, and cloud-agnostic deployment strategy.

---

## 1. Local Development Topology (Docker Compose)

For local development and hackathon evaluation, Paraxis AI runs with minimal operational friction:
- **`postgres` container**: `pgvector/pgvector:pg16` on host port `5432` with named volume `postgres_data` and automatic init script (`infrastructure/postgres/init-pgvector.sql`).
- **`redis` container**: `redis:7-alpine` on host port `6379` with named volume `redis_data`.
- **Applications**: Run either natively via hot-reloading dev servers or in optional containerized profiles:
  - `backend/core`: `python manage.py runserver 0.0.0.0:8000`
  - `backend/intelligence`: `uvicorn main:app --port 8001 --reload`
  - `frontend`: `npm run dev` on port `3000`

---

## 2. Enterprise Cloud-Agnostic Topology (Target Production)

Paraxis AI is intentionally designed to avoid vendor lock-in and runs cleanly on any standard container platform (AWS, GCP, Azure, or private cloud):

```mermaid
flowchart TD
    subgraph PublicInternet["Public Internet"]
        Users["Campus Users / Staff"]
    end

    subgraph Edge["Edge Infrastructure"]
        Cloudflare["Cloudflare / CDN<br/>(WAF, DDoS, Edge SSL)"]
        ALB["Application Load Balancer / Ingress"]
    end

    subgraph AppCluster["Container Cluster (ECS / Cloud Run / Kubernetes)"]
        WebPods["Next.js Web Service (Port 3000)<br/>Auto-scaled stateless pods"]
        CorePods["Django Core Service (Port 8000)<br/>Gunicorn / Uvicorn worker pods"]
        IntelPods["FastAPI Intelligence Service (Port 8001)<br/>High-concurrency async pods"]
    end

    subgraph ManagedData["Managed State & Persistence"]
        RDS["Managed PostgreSQL 16 + pgvector<br/>(Primary + Read Replica)"]
        ElastiCache["Managed Redis 7 Cluster<br/>(Multi-AZ)"]
        S3Bucket["Object Storage (S3 / GCS)<br/>(Encrypted Media & Document Uploads)"]
    end

    Users --> Cloudflare --> ALB
    ALB -->|/| WebPods
    ALB -->|/api/v1/auth, /api/v1/incidents| CorePods
    ALB -->|/api/v1/intelligence, /api/v1/events/stream| IntelPods

    IntelPods -->|Internal Network Call| CorePods
    CorePods --> RDS
    IntelPods --> RDS
    CorePods --> ElastiCache
    IntelPods --> ElastiCache
    CorePods --> S3Bucket
```

---

## 3. High Availability & Scaling Characteristics

1. **Next.js Web**: Fully stateless; scales horizontally based on CPU / HTTP request counts.
2. **Django Core**: Stateless application nodes. Persistent state lives in PostgreSQL and Redis.
3. **FastAPI Intelligence**: I/O-bound async workers communicating with LLM providers; horizontally scales based on active agent concurrency.
4. **PostgreSQL + pgvector**: Scaled vertically for memory and IOPS; read replicas used for analytics and read-heavy reporting queries.
