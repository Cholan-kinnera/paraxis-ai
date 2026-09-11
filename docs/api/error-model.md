# Error Model Specification — Paraxis AI

> **Purpose**: Standardized API error envelopes, error codes, and leakage prevention rules.

---

## 1. Unified Error Envelope

All error responses (HTTP 4xx and 5xx) across Django Core and FastAPI Intelligence adhere to this strict JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request body failed schema validation.",
    "request_id": "req_872c91b2-1847-49f2",
    "timestamp": "2026-09-11T12:00:00Z",
    "details": [
      {
        "field": "room_number",
        "issue": "Room number must be a non-empty string"
      }
    ]
  }
}
```

---

## 2. Standard Error Codes

| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| **`UNAUTHENTICATED`** | 401 | Missing, invalid, or expired JWT access token. |
| **`PERMISSION_DENIED`** | 403 | User role or policy engine denies access to resource. |
| **`TENANT_NOT_FOUND`** | 404 | Campus or organization context invalid or inaccessible. |
| **`RESOURCE_NOT_FOUND`** | 404 | Requested entity ID does not exist in tenant scope. |
| **`VALIDATION_FAILED`** | 400 | Request body or query parameters violate schema. |
| **`POLICY_VIOLATION`** | 422 | Proposed action rejected by Deterministic Policy Engine. |
| **`RATE_LIMIT_EXCEEDED`** | 429 | Too many requests submitted within rate window. |
| **`INTERNAL_ERROR`** | 500 | Unhandled server error. |

---

## 3. Strict Information Leakage Prevention

> [!CRITICAL]
> **Zero Internal Leakage Invariant**:
> Error responses must **NEVER** expose:
> - Python stack traces or traceback lines.
> - Database error strings or SQL queries.
> - Secret keys or environment variables.
> - Internal agent prompts or chain-of-thought tokens.
> 
> Uncaught exceptions are intercepted by global exception handlers, logged internally with full context and `request_id`, and returned to the client as a generic `INTERNAL_ERROR` referencing the `request_id`.
