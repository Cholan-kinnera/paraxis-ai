# AGENTS.md — Autonomous Coding Agent Guidelines

> **Target Audience**: Autonomous AI coding agents, pair-programming assistants, and human engineers contributing to the **Paraxis AI** codebase.  
> **Status**: INVARIANT MANDATE. All guidelines in this document are strictly binding.

---

## 1. Product Context & Operational Mission

Paraxis AI is **"The Intelligent Operational Layer for Modern Campuses"**.  
Core promise: *"See what is happening. Understand what matters. Coordinate what happens next."*

Paraxis AI sits above existing campus workflows to ingest multi-source operational events (unstructured incident reports, attendance anomalies, hostel/mess operations, and safety concerns), enrich them with contextual campus graphs, evaluate priority, and coordinate verified remediation workflows.

---

## 2. Non-Negotiable Architectural Invariants

### 2.1 The Django / FastAPI Boundary
- **Django Core (`backend/core`)**: Owns canonical business state, database persistence, tenancy, organizations, users, roles, permissions, audit logs, SLA calculation, and transactional APIs.
- **FastAPI Intelligence (`backend/intelligence`)**: Owns AI reasoning, LangGraph stateful workflows, model routing, pgvector semantic retrieval, and agent tool execution.
- **The Golden Rule**: **The LLM is NEVER the source of truth.**  
  The AI *proposes*. The domain layer *validates*. The policy engine *authorizes*. The system *executes*.  
  FastAPI and LangGraph must NEVER write directly to core relational tables bypassing Django's domain authorization.

### 2.2 Multi-Tenancy Invariant
- Data hierarchy is strictly: `Organization -> Campus -> Resources (Departments, Buildings, Rooms, Incidents)`.
- Tenant context MUST ALWAYS be derived from the authenticated caller's security token.
- **NEVER** trust client-supplied tenant identifiers in payload bodies or query parameters.
- Every ORM query and vector search must be scoped with tenant filters (`organization_id`, `campus_id`).

### 2.3 Tool Safety & Policy Invariant
Agents interact with the world strictly via typed, registered tools.
- **Prohibited Agent Capabilities**:
  - NO arbitrary SQL execution or raw ORM access.
  - NO arbitrary shell or system execution.
  - NO unrestricted HTTP or network egress.
  - NO direct writes to the filesystem outside temporary scratch directories.
  - NO unmonitored or unthrottled outbound notifications.
- **Policy Engine Gate**: Every consequential tool call must be evaluated against the Policy Engine:
  - `ALLOW`: Safe, idempotent, pre-approved actions (e.g., query room status, create routine draft).
  - `REQUIRE_HUMAN_APPROVAL`: Consequential, financial, disciplinary, or public communication actions.
  - `DENY`: Actions violating security constraints, safety policies, or tenant bounds.

---

## 3. Directory Ownership

| Path | Primary Owner | Allowed Scope of Changes |
| :--- | :--- | :--- |
| `frontend/` | Frontend Team | Next.js components, pages, TanStack Query hooks, Tailwind styles. |
| `backend/core/` | Core Backend Team | Django models, DRF serializers, domain services, migrations, audit hooks. |
| `backend/intelligence/` | AI Engineering | FastAPI endpoints, LangGraph nodes, prompt templates, tool wrappers. |
| `packages/contracts/` | Platform Architecture | Shared schemas, Pydantic models, event interfaces. |
| `packages/ui/` | Design Systems | Reusable presentation primitives and design tokens. |
| `docs/decisions/` | Principal Architects | Architecture Decision Records (ADR-001+). Required for architectural changes. |
| `docs/` | All Engineers | System documentation, runbooks, and design specifications. |

---

## 4. Prohibited Agent Behaviors (Strict Enforcements)

When executing tasks in this repository, agents **MUST NEVER**:
1. **Rewrite Architecture without an ADR**: Never change technology stacks, service boundaries, or data ownership models without an accepted Architecture Decision Record in `docs/decisions/`.
2. **Refactor Unrelated Code**: Limit changes strictly to the explicit requirements of the assigned task. Never perform unsolicited "code cleanup" across unrelated files.
3. **Introduce Unnecessary Dependencies**: Do NOT add new third-party libraries, NPM packages, or Python packages without explicit human approval and security review.
4. **Bypass Authorization**: Never write bypass logic around tenant filters, RBAC checks, or the Policy Engine to "make tests pass."
5. **Directly Mutate Production/Core Data from FastAPI**: The intelligence platform must call Core Platform internal APIs with service identity to request state mutations.
6. **Expose Internal Prompts or Chain-of-Thought**: Raw LLM internal reasoning chains must never be leaked to public API responses or user interfaces. Surface structured summaries, verified evidence, and proposed actions instead.
7. **Disable Tests or Weaken Assertions**: Never delete, skip, or weaken existing tests.
8. **Expose Secrets**: Never commit real API keys, passwords, or credentials. Use `.env.example` placeholders.
9. **Silently Change Public APIs**: Never modify existing API request/response contracts without versioning (`/api/v1/` vs `/api/v2/`).
10. **Block Engineering on Figma**: Never refuse, pause, or delay implementation citing missing or unapproved Figma designs. Figma is strictly an optional visual reference; engineers must proceed immediately using documented product requirements, design tokens, and existing UI components.

---

## 5. Coding & Style Conventions

### Python (Core & Intelligence)
- Target Python: 3.12+ (System: 3.14.6)
- Typing: Strict type hints (`typing`, `pydantic v2`) on all function signatures and public APIs.
- Formatting: Follow PEP 8 and Black/Ruff formatting guidelines.
- Error Handling: Use structured domain exceptions. Never use bare `except: pass`.

### TypeScript & React (Web)
- Target: TypeScript 5+, React 18+, Next.js 14+ (App Router).
- Workflow: Follow the decoupled sequence: `Documentation -> Design System -> API Contracts -> Implementation`. Figma is strictly an optional visual reference, never a blocking prerequisite.
- Components: Functional components with explicit prop types.
- State & Data Fetching: TanStack Query for server state; React Hook Form + Zod for form validation.
- Styling: Tailwind CSS with shadcn/ui primitives. Avoid ad-hoc inline styles.

---

## 6. Observability & Tracing Requirements

Every request and agent workflow must preserve correlation headers across service boundaries:
- `X-Request-ID`: Client/HTTP request correlation ID.
- `X-Trace-ID`: Distributed OpenTelemetry trace ID.
- `X-Tenant-ID`: Active organization/campus identifier.
- `X-Agent-Run-ID`: Unique identifier for the LangGraph execution instance.
- `X-Tool-Call-ID`: Unique invocation identifier for tool telemetry.

All logs must be structured JSON containing these identifiers. Never log passwords, tokens, full student names in safety contexts, or raw PII.

---

## 7. Definition of Done (DoD)

A task or PR is considered **Done** ONLY when:
- [ ] Requirements specified in the issue/prompt are completely satisfied.
- [ ] Architectural boundaries (Django Core vs FastAPI Intelligence) are strictly respected.
- [ ] Domain models and API schemas are fully typed and documented.
- [ ] Tenant isolation is guaranteed across all queries.
- [ ] Unit tests and negative/edge-case tests have been written and pass.
- [ ] AI evaluations have been updated if prompt or tool definitions were altered.
- [ ] Structured logging and error handling are implemented (no naked exceptions).
- [ ] Documentation in `docs/` is updated to reflect any new behavior or APIs.
- [ ] No secrets, debug logs, or temporary files are left behind.
