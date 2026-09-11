# Environments & Configuration — Paraxis AI

> **Purpose**: Environment taxonomy, configuration parameters, and secret management across environments.

---

## 1. Environment Taxonomy

| Environment | Purpose | Database | LLM Provider | Observability |
| :--- | :--- | :--- | :--- | :--- |
| **`development`** | Local engineer machines | Docker Compose (`postgres`, `redis`) | Mock or Google Gemini (Dev Key) | Console logs, local OpenTelemetry |
| **`test` / `ci`** | Automated GitHub Actions CI | Ephemeral Docker containers | Strict `MockModelAdapter` | Junit / coverage reports |
| **`staging`** | Pre-production validation | Managed Cloud Postgres + Redis | Real Gemini / OpenAI models | Full OpenTelemetry tracing |
| **`production`** | Production SaaS instances | High-availability Multi-AZ RDS | Production LLM quotas + fallback | Production APM (Datadog / Grafana) |

---

## 2. Secrets Management

- **Local Development**: `.env` file (copied from `.env.example`, git-ignored).
- **Staging & Production**: Cloud Secret Manager (AWS Secrets Manager / GCP Secret Manager) injected at container startup as environment variables. Real secrets are never stored on disk.
