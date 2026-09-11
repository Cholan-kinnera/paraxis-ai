# Integration Architecture — Paraxis AI

> **Purpose**: Ingestion channels, external integrations, webhook protocols, and campus SIS/LMS connectors.

---

## 1. External Ingestion Gateways

Paraxis AI receives operational triggers and reports through multiple interfaces:
1. **Web Command Center & Student Portal**: Direct authenticated JSON payloads over HTTPS.
2. **Campus Email Ingestion (Proposed)**: Inbound SMTP parsing converting support emails (e.g., `wifi-support@campus.edu`) into unclassified incidents.
3. **IoT Sensor & Network Telemetry (Proposed)**: Webhook endpoints ingesting telemetry alerts (e.g., network switch down, HVAC temperature thresholds).
4. **Third-Party Integrations**: Slack / Microsoft Teams incident reporting bots.

---

## 2. Webhook Dispatch Protocol

When consequential events occur (e.g., `INCIDENT_ESCALATED`, `TASK_ASSIGNED`), Paraxis AI can dispatch signed webhooks to external departmental tools:
- **Header Security**:
  - `X-Paraxis-Signature`: HMAC-SHA256 signature calculated over the payload using a shared tenant secret.
  - `X-Paraxis-Event-ID`: Unique event UUID for idempotency.
  - `X-Paraxis-Timestamp`: Epoch millisecond timestamp to prevent replay attacks (tolerance: 300 seconds).
- **Retry & Backoff**: Exponential backoff (10s, 30s, 2m, 10m, 1h) with dead-letter queueing in Redis upon repeated failure.
- **SSRF Resistance**: Webhook destinations must resolve to public IP addresses outside internal RFC 1918 ranges.

---

## 3. Student Information System (SIS) / ERP Connectors (Proposed)

STATUS: PROPOSED

To support seamless enterprise adoption without replacing existing university systems, Paraxis AI defines standard connector interfaces:
- **SIS Connector**: Read-only periodic sync or SCIM 2.0 provisioning for students, faculty, and roster allocations.
- **Facility Management Sync**: Bidirectional sync with legacy work-order software (e.g., SAP PM, Maximo) via typed adapters.
