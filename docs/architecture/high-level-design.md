# High-Level Design (HLD) — Paraxis AI

> **Purpose**: Detailed component interactions, end-to-end data flows, lifecycle state machines, and failure boundaries for Paraxis AI.

---

## 1. System Interaction Topology

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student / Reporter
    participant Web as Next.js Web App
    participant Core as Django Core Platform
    participant DB as PostgreSQL + pgvector
    participant Redis as Redis Pub/Sub
    participant Intel as FastAPI Intelligence (LangGraph)
    actor Staff as Maintenance / IT Staff

    Student->>Web: Submits "Wi-Fi is down in Block B, Room 204"
    Web->>Core: POST /api/v1/incidents (with Bearer JWT)
    Core->>Core: Validate Token & Tenant Scope (Org/Campus)
    Core->>DB: INSERT INTO incidents (status=INGESTED)
    Core->>Redis: PUBLISH campus:events (type=INCIDENT_CREATED)
    Core-->>Web: 201 Created (incident_id, status=INGESTED)

    Redis->>Intel: Trigger Agent Orchestration
    activate Intel
    Intel->>Intel: 1. UNDERSTAND: Extract Intent & Entities (Block B, Room 204, Wi-Fi)
    Intel->>DB: 2. CONTEXTUALIZE: Query Campus Graph & pgvector (Assets, Policies)
    Intel->>DB: 3. DETECT: Find Related/Duplicate Incidents
    Intel->>Intel: 4. REASON & PLAN: Assess Priority=MEDIUM, Propose Action=CREATE_TASK
    Intel->>Intel: 5. POLICY CHECK: Evaluate Policy(CREATE_TASK, routine_it_repair) -> ALLOW
    Intel->>Core: 6. ACT: POST /internal/v1/tasks (via Internal Service Auth)
    Core->>DB: INSERT INTO tasks (assigned_to=IT_NETWORK, status=ASSIGNED)
    Core->>DB: INSERT INTO slas (deadline=Now + 2h, status=ACTIVE)
    Core->>DB: INSERT INTO audit_logs (actor=AgentRun, action=TASK_CREATED)
    Core->>Redis: PUBLISH campus:events (type=TASK_ASSIGNED, incident_id)
    deactivate Intel

    Redis-->>Web: SSE Live Telemetry Update (Action Taken, SLA Started)
    Redis-->>Staff: Push Notification to IT Operations Team
    Staff->>Web: Acknowledges & Dispatches Technician
    Staff->>Web: Completes Repair & Submits Proof
    Web->>Core: POST /api/v1/incidents/{id}/resolve
    Core->>DB: UPDATE incidents (status=RESOLVED)
    Core->>DB: UPDATE slas (status=MET)
    Core->>Redis: PUBLISH campus:events (type=INCIDENT_RESOLVED)

    Redis->>Intel: Trigger Memory & Insight Mining
    activate Intel
    Intel->>DB: 7. REMEMBER: Store Incident Embedding in operational_memory
    Intel->>DB: 8. INSIGHT: Cluster historical AP failures in Block B
    Intel->>DB: INSERT INTO operational_insights ("AP-04 recurring failure pattern detected")
    deactivate Intel
```

---

## 2. Core Request & Authentication Flows

### 2.1 User Authentication Flow
1. User logs in via `/api/v1/auth/token/` with credentials.
2. Django Core verifies credentials against `User` table, checking active status and assigned `Role`.
3. Django Core returns signed RS256/HS256 JWT containing:
   - `sub`: User UUID
   - `org_id`: Organization UUID
   - `campus_id`: Active Campus UUID
   - `roles`: Assigned roles (`STUDENT`, `STAFF`, `ADMIN`, etc.)
   - `exp`: Short-lived expiration (15 minutes).
4. Web client attaches this token in `Authorization: Bearer <token>` for all subsequent requests.

### 2.2 Service-to-Service Authentication Flow
1. FastAPI Intelligence calls Django Core internal endpoints (`/internal/v1/*`) to execute approved domain mutations.
2. The request includes:
   - `X-Internal-Service-Key`: Pre-shared high-entropy cryptographic service secret.
   - `X-Agent-Run-ID`: LangGraph execution identifier.
   - `X-Actor-User-ID`: The original user on whose behalf the agent is running.
3. Django Core's `InternalServiceAuthentication` middleware verifies the service key and sets the request context.

---

## 3. Real-Time Event & Telemetry Architecture

```mermaid
flowchart LR
    subgraph Producers
        CoreService["Django Core (Domain Mutations)"]
        AgentEngine["FastAPI (Agent Reasoning Steps)"]
    end

    subgraph Broker["Redis Pub/Sub"]
        CampusChannel["Channel: campus:{campus_id}:events"]
        IncidentChannel["Channel: incident:{incident_id}:agent"]
    end

    subgraph Streaming
        SSEHandler["FastAPI SSE Endpoint<br/>/api/v1/events/stream"]
    end

    subgraph Consumers
        BrowserClient["Command Center Browser UI<br/>(EventSource Listener)"]
    end

    CoreService -->|Publish| CampusChannel
    AgentEngine -->|Publish| IncidentChannel
    CampusChannel --> SSEHandler
    IncidentChannel --> SSEHandler
    SSEHandler -->|HTTP/2 SSE Stream| BrowserClient
```

---

## 4. Failure Boundaries & Resilience

| Boundary | Failure Mode | Resilience Strategy | Impact |
| :--- | :--- | :--- | :--- |
| **AI Provider Outage** | External LLM API (Google/OpenAI) times out or returns 500 | Automatic fallback to secondary provider or MockModelAdapter; mark agent run as DEGRADED; fallback to rule-based triage. | Incidents still created; routing falls back to default department queue. |
| **FastAPI Down** | Intelligence service crashes or restarts | Django Core operates independently; incidents persist with status `PENDING_AGENT`; background retry reconciles unprocessed events. | Zero data loss; automated triage delayed until recovery. |
| **Redis Down** | Cache & Pub/Sub unavailable | Core falls back to direct database reads; live SSE streaming temporarily disables; UI gracefully reverts to polling. | Realtime UI updates delayed; core operations intact. |
| **PostgreSQL Down** | Primary database unavailable | Monitored health checks fail; load balancer halts traffic; persistent volume preserves data; read replica failover in enterprise setup. | System enters 503 Maintenance state. |

---

## 5. Deployment Boundaries

- **Development**: All services orchestrated locally via `docker-compose.yml` (`postgres`, `redis`) with native runtimes (`apps/core` on 8000, `apps/intelligence` on 8001, `apps/web` on 3000).
- **Production / Enterprise**: Cloud-agnostic containerized deployment (e.g., AWS ECS, GCP Cloud Run, or generic Kubernetes) with managed PostgreSQL 16 (with pgvector) and managed Redis.
