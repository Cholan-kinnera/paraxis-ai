# Contributing to Paraxis AI

Thank you for contributing to Paraxis AI. This document outlines our engineering standards, contribution lifecycle, and pull request policies.

---

## 1. Branching Strategy

We follow a structured trunk-based development model:
- `main`: Production-ready, stable codebase. All direct pushes to `main` are restricted.
- Feature branches: Created from `main` using descriptive naming conventions:
  - `feat/feature-name`: New features or capabilities.
  - `fix/bug-description`: Bug fixes or defect patches.
  - `arch/architectural-change`: Structural changes accompanied by an ADR.
  - `docs/documentation-update`: Documentation additions or revisions.
  - `eval/agent-benchmark`: AI evaluation datasets or benchmark updates.

---

## 2. Commit Message Conventions

We enforce Conventional Commits:
```
<type>(<scope>): <short descriptive summary>

[optional body explaining rationale and consequences]

[optional footer(s) referencing issue IDs]
```

### Supported Types:
- `feat`: A new feature for the user or platform.
- `fix`: A bug fix.
- `arch`: Architectural modification (must reference an ADR).
- `docs`: Documentation only changes.
- `style`: Formatting, missing semicolons, etc. (no production code change).
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `test`: Adding missing tests or correcting existing tests.
- `chore`: Tooling, dependency, or configuration updates.

---

## 3. Pull Request Requirements

Every Pull Request must include:
1. **Clear Description**: Context, problem solved, and link to issue.
2. **Architectural Adherence**: Explicit affirmation that the Django/FastAPI boundary and tenant isolation invariants are respected.
3. **Automated Tests**:
   - Backend: Unit and integration tests using `pytest`.
   - Frontend: Unit and component tests using `Vitest`.
   - E2E: Critical user flows covered using `Playwright`.
4. **Documentation**: Updates to corresponding files in `docs/` (PRD, HLD, LLD, API specs).
5. **Security Review**: Check for OWASP Top 10, prompt injection vectors, and tenant leakage risks.
6. **No Regressions**: CI pipeline must pass cleanly with 0 linter errors and 0 failing tests.
7. **Decoupled Visual Design**: Figma designs are strictly optional visual references. Missing or pending Figma mockups must never block a PR or feature implementation. Rely on documented product requirements, API contracts, and design system tokens.

---

## 4. Architecture Decision Records (ADRs)

If a proposed change introduces:
- A new database, storage engine, or caching layer
- A new third-party framework or major library
- A change to the service boundary between Django and FastAPI
- A modification to the tenant isolation model
- A change in the tool safety or policy engine model

You **must** submit a new ADR under `docs/decisions/` formatted according to our standard ADR template (`Title`, `Status`, `Context`, `Problem`, `Decision`, `Alternatives`, `Consequences`, `Security`, `Operations`, `Date`, `Owner`).

---

## 5. AI Evaluation Requirements

Any modification to:
- Prompt templates
- Model routing parameters
- LangGraph node logic
- Agent tool definitions or schemas

Must be accompanied by offline evaluation benchmark results in `tests/evaluation/` verifying:
- Extraction accuracy does not degrade.
- Duplicate detection precision and recall remain within accepted thresholds.
- Prompt injection defenses remain uncompromised.
- JSON output structure adheres strictly to the defined Pydantic schema.
