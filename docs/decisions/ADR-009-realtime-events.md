# ADR-009: Realtime Operational Telemetry via Redis Pub/Sub and SSE

- **Status**: ACCEPTED
- **Date**: 2026-09-11
- **Owner**: Founding Principal Architect & Engineering Team

---

## Context
Campus operators in the Command Center require immediate visibility when incidents are reported, agent reasoning steps progress, priority changes, or tasks are assigned. Similarly, students reporting issues need live feedback as their report transitions from ingestion to resolution.

## Problem
Traditional polling creates unnecessary database strain, introduces high latency, and fails to give users the feeling of an active, responsive intelligent operational layer. Full bidirectional WebSockets across all clients introduce connection management overhead, sticky session complexities, and firewall challenges.

## Decision
1. **Server-Sent Events (SSE) for Frontend Streaming**:
   - Web clients connect via HTTP/2 SSE endpoints (`/api/v1/events/stream?campus_id=...` or `/api/v1/incidents/{id}/stream`).
   - SSE provides clean, unidirectional real-time event delivery with automatic reconnection and zero custom socket protocol overhead.
2. **Redis Pub/Sub as Event Backbone**:
   - When Django Core commits an incident event, task assignment, or SLA breach, it publishes an event envelope to a Redis channel (`campus:{campus_id}:events`).
   - When FastAPI executes an agent node or tool call, it publishes real-time execution steps to an incident-specific channel (`incident:{incident_id}:agent`).
   - FastAPI and Core SSE handlers subscribe to Redis channels and fan out events to authenticated client streams.
3. **WebSockets Reserved for Bidirectional Realtime (Proposed)**:
   - Status: PROPOSED. WebSockets will only be introduced in Phase 5 if two-way peer communication (e.g., live security dispatch chat) is required.

## Alternatives Considered
1. **Short Polling (every 3 seconds)**:
   - *Rejected*: Inefficient; causes high database load and poor UX.
2. **Kafka / RabbitMQ**:
   - *Rejected*: Heavy infrastructure overhead; Redis is already deployed for caching and easily handles campus event scale.

## Consequences
- **Positive**:
  - Live, low-latency UI updates in the Command Center.
  - Transparent agent reasoning visualization (decision summaries and actions, not raw chain-of-thought).
  - Simple horizontal scaling using Redis pub/sub.
- **Negative**:
  - Requires maintaining persistent HTTP connections on server instances.

## Security Implications
SSE connections require valid JWT authentication. Stream topics are strictly authorized to match the user's campus scope and role permissions.
