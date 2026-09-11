# API Design Guidelines — Paraxis AI

> **Purpose**: RESTful conventions, endpoint taxonomy, naming conventions, pagination, idempotency, and status code standards.

---

## 1. Endpoint Namespace Conventions

- **Public & Client APIs**: Prefixed with `/api/v1/`
  - Examples: `POST /api/v1/incidents/`, `GET /api/v1/tasks/`, `GET /api/v1/events/stream`
- **Internal Service-to-Service APIs**: Prefixed with `/internal/v1/`
  - Examples: `POST /internal/v1/tasks/dispatch`, `POST /internal/v1/incidents/{id}/enrich`
  - Gated by mutual service authentication (`X-Internal-Service-Key`); never exposed to the public internet.

---

## 2. Standard HTTP Verbs & Status Codes

- `GET`: Retrieve resource or collection. (200 OK, 404 Not Found)
- `POST`: Create resource or trigger action. (201 Created, 202 Accepted, 400 Bad Request)
- `PATCH`: Partially update resource fields. (200 OK, 400 Bad Request)
- `DELETE`: Soft delete resource. (204 No Content)

---

## 3. Pagination & Filtering

All collection endpoints (`GET /api/v1/incidents/`) adhere to standard cursor or limit-offset pagination:
```json
{
  "count": 142,
  "next": "https://api.paraxis.ai/api/v1/incidents/?limit=20&offset=20",
  "previous": null,
  "results": [ ... ]
}
```

---

## 4. Idempotency Keys

All state-mutating endpoints accept an optional header:
`Idempotency-Key: <UUID>`
When provided, identical subsequent requests within 24 hours return the cached response without re-executing business logic.
