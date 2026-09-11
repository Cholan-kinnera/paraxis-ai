# Authentication & Identity Protocols — Paraxis AI

> **Purpose**: JWT specifications, token rotation, service-to-service credentials, and session lifecycles.

---

## 1. User Authentication (JWT)

- **Access Token**: Short-lived (15 minutes), signed RS256/HS256 JWT.
  - Header: `{ "alg": "HS256", "typ": "JWT" }`
  - Claims:
    ```json
    {
      "sub": "u_948a1204-...",
      "email": "aarav.patel@campus.edu",
      "org_id": "org_71092a...",
      "campus_id": "camp_8819a...",
      "roles": ["STUDENT"],
      "exp": 1789123800,
      "iat": 1789122900
    }
    ```
- **Refresh Token**: Long-lived (7 days), stored in HTTP-only Secure SameSite cookies or returned in encrypted response payload for mobile clients. Revocable in Redis.

---

## 2. Internal Service Authentication

When FastAPI Intelligence invokes Django Core internal endpoints (`/internal/v1/*`), it provides:
- Header: `X-Internal-Service-Key: <high-entropy-secret>`
- Header: `X-Actor-User-ID: <original-user-uuid>`
- Header: `X-Agent-Run-ID: <agent-run-uuid>`

Django Core verifies the service key against `INTELLIGENCE_INTERNAL_TOKEN` and scopes the execution context to the specified actor user.
