# Paraxis AI — Backend Production Deployment Runbook

> **Target Audience**: Infrastructure engineers, DevOps, and backend platform operators.  
> **Deployment Targets**: Supabase (PostgreSQL 16 + pgvector), Render (Django Core & FastAPI Intelligence Web Services), Managed Redis.

---

## 1. Architectural Topology & Service Boundaries

```mermaid
flowchart TD
    subgraph Clients ["Public Clients & Frontend"]
        NextWeb["Next.js Web Frontend<br/>(Deployed Separately)"]
    end

    subgraph RenderPlatform ["Render Cloud Platform"]
        subgraph DjangoService ["Service 1: paraxis-core (Django 6 + DRF)"]
            CoreAPI["REST APIs (/api/v1/)<br/>Auth / Tenancy / Graph / Incidents / Tasks / SLAs / Memory"]
            CoreHealth["Liveness Probe (/api/v1/health/)"]
        end

        subgraph FastAPIservice ["Service 2: paraxis-intelligence (FastAPI + LangGraph)"]
            OrchestrationAPI["Orchestrator (/api/v1/orchestrate/)<br/>Tools / RAG / Reasoning"]
            IntelligenceHealth["Liveness Probe (/api/v1/health)"]
            LangGraphEngine["LangGraph State Engine<br/>(Single-Instance MemorySaver)"]
        end
    end

    subgraph DataTier ["Managed Cloud Infrastructure"]
        SupabaseDB[("Supabase PostgreSQL 16<br/>+ pgvector (768-dim HNSW)<br/>Session Pooler (Port 5432, IPv4)")]
        RedisStore[("Managed Redis 7+<br/>(Optional Pub/Sub / Caching)")]
        AIProviders["External AI Gateway<br/>(Google Gemini / OpenAI)"]
    end

    NextWeb -->|HTTPS / JWT| CoreAPI
    NextWeb -->|HTTPS / JWT| OrchestrationAPI
    
    FastAPIservice -->|Internal HTTPS / DjangoCoreClient| CoreAPI
    DjangoService -->|Encrypted PostgreSQL + pgvector| SupabaseDB
    DjangoService -.->|Optional Cache / Events| RedisStore
    FastAPIservice -->|HTTPS / Ephemeral Tokens| AIProviders
```

---

## 2. Supabase PostgreSQL + pgvector Connection Strategy

### 2.1 Recommended Connection Method: Supabase Session Mode Pooler
For deploying Django Core on Render connected to Supabase, the **Session Mode Connection Pooler** on port **5432** is the canonical recommendation.

- **Connection URL Format**:
  ```text
  postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
  ```
- **Rationale & Technical Criteria**:
  1. **IPv4 / IPv6 Routing**: Render web service containers resolve and route outbound traffic over IPv4. Direct Supabase endpoints (`db.[project-ref].supabase.co`) frequently resolve to IPv6-only addresses in many AWS regions (requiring a paid IPv4 add-on). The Supabase Supavisor pooler host (`aws-0-[region].pooler.supabase.com`) provides full dual-stack IPv4/IPv6 support at zero additional cost.
  2. **Session Mode (Port 5432) vs. Transaction Mode (Port 6543)**: Django's ORM relies on session-level features, server-side cursors, prepared statements, and connection pooling (`CONN_MAX_AGE=60`). Session mode (port 5432) is fully compatible with Django ORM, whereas Transaction mode (port 6543) breaks prepared statements.
  3. **SSL Requirement**: Supabase strictly requires encrypted transport (`sslmode=require`). Django Core automatically extracts `sslmode=require` from the `DATABASE_URL` query string and configures PostgreSQL `OPTIONS`.
  4. **pgvector Compatibility**: pgvector cosine distance queries and HNSW index lookups execute seamlessly over the session pooler.

---

## 3. Migration & Static File Strategy

### 3.1 Migration Strategy (Render Free Startup Hook)
- **Current Render Free Deployment**: Render Free web services do not support a dedicated Pre-Deploy Command. Migrations are executed automatically inside the Django container entrypoint ([`backend/core/entrypoint.sh`](file:///home/cholan0415/Projects/paraxis-ai/backend/core/entrypoint.sh)) before the Gunicorn WSGI server is invoked:
  ```bash
  python manage.py migrate --noinput
  ```
- **Strict Startup Failure Behavior**: If PostgreSQL/Supabase is unreachable or if any migration fails, the container process immediately aborts (`set -eu`), preventing Gunicorn from starting in a broken or un-migrated state.
- **Idempotency**: Django migrations are strictly idempotent. When subsequent deployments or container restarts occur without schema changes, `migrate --noinput` completes near-instantly with zero operational side-effects.
- **Data Integrity**: Production data is **never** seeded automatically during startup (`seed_dev_data` or fixtures are strictly prohibited in container startup).
- **Future Paid Tier Optimization**: On paid Render tiers (Starter/Standard), migrations may optionally be moved out of the container lifecycle into Render's native Pre-Deploy Command (`python manage.py migrate --noinput`), ensuring zero-downtime rolling deploys. The current implementation remains completely self-contained and fully functional on the Free plan.

### 3.2 Static File Strategy
- **Canonical Strategy**: **Baked during Docker Image Build**.
- In [`backend/core/Dockerfile`](file:///home/cholan0415/Projects/paraxis-ai/backend/core/Dockerfile), `python manage.py collectstatic --noinput` executes at build time, placing static assets into `/app/backend/core/staticfiles`.
- No redundant static collection occurs during deployment or container startup.

---

## 4. Render Service Configurations

### 4.1 Service 1: `paraxis-core` (Django Web Service)
- **Environment**: Docker
- **Docker Build Context**: `.` (Repository root)
- **Dockerfile Path**: `backend/core/Dockerfile`
- **Entrypoint**: Runs `python manage.py migrate --noinput` followed by `exec gunicorn`
- **Health Check Path**: `/api/v1/health/`
- **Auto-Deploy**: Enabled on `main` branch
- **Instance Sizing**: Free (or Starter/Standard)
- **Dynamic Port**: Binds to `0.0.0.0:$PORT` via Gunicorn.

### 4.2 Service 2: `paraxis-intelligence` (FastAPI Web Service)
- **Environment**: Docker
- **Docker Build Context**: `.` (Repository root)
- **Dockerfile Path**: `backend/intelligence/Dockerfile`
- **Health Check Path**: `/api/v1/health`
- **Auto-Deploy**: Enabled on `main` branch
- **Instance Sizing**: Starter ($7/mo) or Standard ($25/mo)
- **Dynamic Port**: Binds to `0.0.0.0:$PORT` via Uvicorn.

---

## 5. MemorySaver Scaling Invariant (CRITICAL)

> [!CAUTION]
> **Single-Instance & Single-Worker Mandate for FastAPI Intelligence**:
> - The FastAPI service currently uses LangGraph's in-process `MemorySaver()` for workflow suspension (`human_gate`) and resumption (`resume_orchestration`).
> - `MemorySaver` maintains thread checkpoints exclusively inside the process RAM of that specific container instance.
> - **Operational Invariant**: The deployment must run with **exactly 1 FastAPI instance** and **`--workers 1`**.
> - **Horizontal Scaling Constraint**: Horizontal scaling (multiple replicas) is **NOT** supported while human-gated workflows rely on in-process `MemorySaver`. Multiple instances would route the resume request to a random instance, causing `404 Checkpoint Not Found` failures.
> - **Future Path**: Before scaling horizontally in future phases, a persistent distributed checkpointer (`PostgresSaver` or Redis checkpointer) must be configured.

---

## 6. Environment Variables Specification

### 6.1 Django Core (`paraxis-core`)
| Variable | Classification | Required? | Description | Example / Default |
| :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Configuration | Required | Runtime environment | `production` |
| `DEBUG` | Security | Required | Disable Django debug mode | `False` |
| `APP_SECRET_KEY` | **SECRET** | Required | Min 32-char cryptographically secure key | *(Secret Random String)* |
| `DATABASE_URL` | **SECRET** | Required | Supabase Session Pooler URL | `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require` |
| `ALLOWED_HOSTS` | Security | Required | Comma-separated hostnames | `core.paraxis.ai,paraxis-core.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Security | Required | Allowed client origins | `https://app.paraxis.ai,https://paraxis.ai` |
| `STATIC_ROOT` | Configuration | Optional | Path to collected static assets | `/app/backend/core/staticfiles` |

### 6.2 FastAPI Intelligence (`paraxis-intelligence`)
| Variable | Classification | Required? | Description | Example / Default |
| :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Configuration | Required | Runtime environment | `production` |
| `DEBUG` | Security | Required | Disable FastAPI debug docs | `False` |
| `CORE_SERVICE_URL` | Configuration | Required | Internal/public URL of Django Core | `https://paraxis-core.onrender.com` |
| `INTELLIGENCE_INTERNAL_TOKEN`| **SECRET** | Required | Internal service secret token | *(Secret Random Token)* |
| `AI_DEFAULT_PROVIDER` | Configuration | Required | Active LLM / embedding provider | `google` *(or `openai` / `mock`)* |
| `GOOGLE_API_KEY` | **SECRET** | Required if Google | Gemini API Key for LLM & embeddings | `AIzaSy...` |
| `OPENAI_API_KEY` | **SECRET** | Optional | OpenAI API Key (if provider is openai) | `sk-...` |
| `CORS_ALLOWED_ORIGINS` | Security | Required | Allowed client origins | `https://app.paraxis.ai,https://paraxis.ai` |
| `REDIS_URL` | **SECRET** | Optional | Redis connection URL | `redis://default:pass@host:6379/0` |

---

## 7. Pre-Provisioning Security & Multi-Tenancy Invariant

- [x] Multi-tenancy isolation strictly enforced from JWT/security token context; zero cross-tenant data access or mutation permitted.
- [x] Epistemological separation maintained: LLMs never write directly to PostgreSQL.
- [x] Zero hardcoded secrets, database passwords, or API keys in the repository or Docker images.
