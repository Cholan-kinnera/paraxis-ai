# API Versioning & Evolution — Paraxis AI

> **Purpose**: API versioning strategy, breaking change policies, and deprecation schedules for Paraxis AI.

---

## 1. URI Path Versioning

We utilize explicit URI path versioning for all public and service endpoints:
- Current stable version: `/api/v1/`
- Internal service version: `/internal/v1/`

---

## 2. Breaking vs. Non-Breaking Changes

### Non-Breaking Changes (Allowed within `v1`):
- Adding new optional fields to a request payload.
- Adding new fields to a response payload.
- Adding new endpoints.

### Breaking Changes (Requires `v2` increment):
- Removing or renaming an existing field in request or response.
- Changing the data type of an existing field.
- Changing authentication mechanisms or required scopes.

---

## 3. Deprecation Policy
- Deprecated endpoints return a standard HTTP header:  
  `Deprecation: true`  
  `Sunset: Wed, 11 Nov 2026 00:00:00 GMT`
- Enterprise customers are guaranteed a minimum of 90 days notice before any v1 endpoint is decommissioned.
