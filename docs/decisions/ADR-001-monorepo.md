# ADR-001: Monorepo Architecture for Paraxis AI

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Paraxis AI comprises a Next.js web application, a Django-based core domain platform, a FastAPI-based intelligence and agent orchestration engine, shared contracts, and deployment infrastructure. During both the hackathon prototyping phase and long-term enterprise SaaS evolution, changes across API contracts, shared schemas, domain events, and UI components must be coordinated efficiently.

## Problem
Splitting the project into separate repositories (polyrepo) creates severe coordination friction: out-of-sync API schemas, multi-repository PR dependencies, fragmented CI/CD pipelines, duplicate typing definitions, and complex local orchestration for new developers. Conversely, a monolithic single-runtime code base forces an unnatural coupling of Django's synchronous ORM with FastAPI's asynchronous agent streaming and Python with TypeScript.

## Decision
Adopt a single unified **monorepo** structure:
- `apps/web`: Next.js frontend application.
- `apps/core`: Django core domain and persistent platform.
- `apps/intelligence`: FastAPI intelligence and LangGraph engine.
- `packages/`: Shared contracts, UI primitives, config, and SDKs.
- `infrastructure/`: Unified Docker, database, and deployment definitions.
- `docs/`: Unified architecture, API, and product documentation.

## Alternatives Considered
1. **Polyrepo (Multiple Git Repositories)**:
   - *Pros*: Independent commit histories and granular access controls.
   - *Cons*: Nightmare schema synchronization, versioning drift, fragmented CI, high developer friction during rapid iteration.
2. **Monolithic Single Application (Django-only with Django Channels)**:
   - *Pros*: Single runtime and language.
   - *Cons*: Poor support for high-concurrency async streaming required by modern LLM agent graphs, suboptimal AI ecosystem integration compared to FastAPI/LangGraph.

## Consequences
- **Positive**:
  - Atomic pull requests spanning frontend, core backend, intelligence, and documentation.
  - Single source of truth for contracts, schemas, and developer workflows.
  - Simplified local setup via a single `docker-compose.yml` and `Makefile`.
- **Negative**:
  - Requires disciplined directory ownership and clear boundaries to prevent circular dependencies.
  - CI pipelines must use path filtering to avoid running all test suites on isolated changes.

## Security Implications
All services share the repository, making secret management crucial. `.gitignore` and `.env.example` must strictly prevent accidental credential commits. Access to deployment workflows must be governed via GitHub branch protections.

## Operational Implications
Local development requires Docker and common toolings (Python, Node). Build pipelines can leverage caching across monorepo packages.

## Migration & Rollback Strategy
If any sub-application eventually requires independent repository hosting (e.g., enterprise customer on-premise SDK), git subtree or git filter-repo can cleanly extract the package preserving commit history.
