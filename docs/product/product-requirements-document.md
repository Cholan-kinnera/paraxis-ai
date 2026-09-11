# Product Requirements Document (PRD) — Paraxis AI

> **Status**: APPROVED FOUNDATION  
> **Version**: 1.0.0  
> **Author**: Founding Principal Architect & Product Team

---

## 1. Problem Statement
Modern university campuses are sprawling physical ecosystems housing thousands of students, faculty, and operational staff. Despite massive annual expenditures, operational workflows remain severely fragmented:
- **Ticketing Black Holes**: Students submit maintenance requests into static portals or WhatsApp groups where issues vanish without updates or accountability.
- **Context Blindness**: Maintenance staff receive tickets like "Wi-Fi broken" without room metadata, asset histories, or awareness that 15 other students in the same wing reported the same issue.
- **Manual Triage Bottlenecks**: Facilities managers spend hours manually categorizing, prioritizing, and reassigning tickets across departments.
- **Zero Institutional Memory**: Chronic infrastructure failures (e.g., an electrical circuit tripping every Tuesday during lab hours) are treated as isolated one-off tickets rather than systemic patterns.

---

## 2. Target Users
1. **Students & Residents**: Need effortless reporting, immediate acknowledgment, and transparent tracking.
2. **Maintenance & IT Technicians**: Need pre-triaged work orders with exact physical context, diagnostic history, and clear instructions.
3. **Department Heads & Wardens**: Need real-time visibility into operational bottlenecks, technician workloads, and facility SLAs.
4. **Campus Leadership (Directors/Admins)**: Need macro-level operational telemetry, safety assurance, and recurring waste/failure patterns.

---

## 3. Jobs to Be Done (JTBD)
- *When a facility or IT issue occurs in my dorm or lab*, I want to report it in plain English from my phone, *so that the right technician is immediately dispatched without bureaucratic delay*.
- *When managing hundreds of daily campus requests*, I want duplicate reports automatically clustered and routine tasks auto-dispatched, *so that my staff only focuses on physical execution and high-priority approvals*.
- *When analyzing annual maintenance budgets*, I want to see which physical assets and buildings consume disproportionate resources, *so that we replace failing equipment proactively*.

---

## 4. Product Vision
To establish Paraxis AI as the sovereign **intelligent operational operating system for physical institutions**, starting with higher education campuses and expanding to hospitals, corporate parks, and civic hubs.

---

## 5. Product Principles
1. **Depth Over Feature Count**: We build reliable, end-to-end coordinated workflows rather than shallow surface-level demo widgets.
2. **Action Over Chat**: The system executes, verifies, and coordinates; it does not stop at conversational replies.
3. **The LLM Proposes, Domain Validates**: Canonical business truth is never governed directly by an AI model.
4. **Transparent Evidence**: The UI exposes clear evidence and decisions, never impenetrable chain-of-thought tokens.

---

## 6. Core Value Proposition
- **90% Reduction in Triage Latency**: From hours of manual assignment to sub-5-second automated contextual dispatch.
- **Zero Duplicate Dispatches**: Intelligent semantic clustering merges redundant reports into a single master operational work order.
- **Proactive Pattern Discovery**: Uncovers chronic hardware and facility failures before catastrophic disruption.

---

## 7. Core Personas
1. **Student** (Reporter / Resident)
2. **Faculty** (Classroom Instructor / Lab Head)
3. **Parent** (Guest / Emergency Contact)
4. **Hostel Warden** (Residential Oversight)
5. **Maintenance Staff** (Electrician, Plumber, HVAC)
6. **IT Support Staff** (Network / Hardware Technician)
7. **Safety Officer** (Security & Emergency Lead)
8. **Campus Administrator** (Operations Director)
9. **Super Administrator** (System / Consortium Governance)

---

## 8. User Journeys
*(Detailed in [user-journeys.md](file:///home/cholan0415/Projects/paraxis-ai/docs/product/user-journeys.md))*
- Reporting a classroom projector outage in 15 seconds.
- Reviewing an automated dispatch in the Command Center.
- Approving an urgent generator repair request exceeding automatic spending thresholds.

---

## 9. Functional Requirements
- **FR-01 (Natural-Language Ingestion)**: Ingest unstructured text reports and extract category, building, room, asset, and urgency.
- **FR-02 (Campus Context Resolution)**: Match extracted entities against the campus physical graph (Buildings, Rooms, Assets).
- **FR-03 (Duplicate Detection)**: Calculate semantic and spatio-temporal similarity to cluster open incidents.
- **FR-04 (Policy Gating)**: Deterministically evaluate proposed actions against campus operational rules (ALLOW, DENY, REQUIRE_HUMAN_APPROVAL).
- **FR-05 (Task & SLA Dispatch)**: Automatically create work orders, assign to departments, and initiate SLA countdowns.
- **FR-06 (Real-Time Command Center)**: Live dashboard streaming active incidents, status timelines, and agent decision summaries via SSE.
- **FR-07 (Operational Memory)**: Cluster resolved incidents to identify recurring failure patterns.

---

## 10. Non-Functional Requirements
- **NFR-01 (Triage Latency)**: End-to-end agent triage, context retrieval, and policy check completed in < 4.0 seconds.
- **NFR-02 (Tenant Isolation)**: 100% mathematical guarantee that no tenant data leaks across campus boundaries in SQL or vector queries.
- **NFR-03 (Availability)**: 99.9% uptime for core domain reporting and status APIs.
- **NFR-04 (Data Integrity)**: Append-only audit logs for all domain mutations and tool calls.

---

## 11. MVP Scope
- Natural-language incident reporting for campus IT and maintenance issues.
- Autonomous entity extraction, campus graph contextualization, and duplicate detection.
- Deterministic policy engine with human approval cards for sensitive actions.
- Command Center live streaming of agent steps, task assignments, and SLA status.
- Verification and resolution lifecycle with operational memory recording.

---

## 12. Hackathon Scope
- Focus on the North-Star Wi-Fi outage workflow:
  `Report "Wi-Fi down in Block B, Room 204" -> Triage -> Contextualize AP-04 -> Detect Duplicate -> Auto-Dispatch Task -> Start SLA -> Resolve -> Surface Historical Pattern`.

---

## 13. Post-Hackathon Scope
- Full implementation of Smart Attendance anomaly detection.
- Smart Hostel & Mess dining headcount forecasting.
- Encrypted confidential safety reporting.
- Native mobile applications (React Native / PWA).

---

## 14. Enterprise Roadmap
*(Detailed in [enterprise-roadmap.md](file:///home/cholan0415/Projects/paraxis-ai/docs/product/enterprise-roadmap.md))*
- SCIM 2.0 / SAML SSO integration.
- Custom enterprise policy builder.
- Multi-campus consortium multi-tenancy.
- Integration connectors for SAP PM, Maximo, and Ellucian Banner.

---

## 15. Success Metrics
- **Mean Time to Triage (MTTT)**: Target < 5 seconds (Baseline: 4.2 hours).
- **Duplicate Detection Precision**: Target > 95%.
- **SLA Breach Reduction**: Target 40% improvement in first-response compliance.
- **Policy Compliance**: 100% adherence to zero unauthorized action executions.

---

## 16. Risks & Mitigation Strategies
- **Risk**: Hallucinated entity extraction sends technician to wrong building.  
  *Mitigation*: Extracted room numbers and building names are strictly fuzzy-matched against canonical campus database records; unverified entities trigger a clarification prompt.
- **Risk**: Prompt injection tricks agent into approving unauthorized purchases.  
  *Mitigation*: Financial actions are hard-gated by the deterministic Policy Engine requiring human supervisor cryptographic approval.

---

## 17. Security Requirements
- JWT token authentication for all user sessions.
- Tenant scoping enforced at the ORM base manager level.
- Rate limiting on incident submission endpoints (max 10 reports/minute per IP/user).

---

## 18. AI Requirements
- Pluggable model gateway supporting Google Gemini, OpenAI, and offline mock models.
- Strict Pydantic v2 structured output validation for all LLM generations.
- Automated offline evaluation benchmarks for extraction, priority, and duplicate detection.

---

## 19. Human Oversight (HITL)
- High financial cost repairs (> $500), safety alerts, and disciplinary flags immediately halt the agent graph at the `human_gate` node.
- The UI presents an interactive approval card with the proposed action, justification, and cost; execution resumes only upon explicit staff approval.

---

## 20. Acceptance Criteria
- [ ] Submitting a natural-language report produces a valid `Incident` row in PostgreSQL.
- [ ] The agent graph extracts building, room, and category without hallucination.
- [ ] Duplicate reports in the same location are linked to the master incident.
- [ ] Policy engine correctly assigns `ALLOW` to routine dispatches and `REQUIRE_HUMAN_APPROVAL` to sensitive actions.
- [ ] Live updates reflect in the Next.js UI via Server-Sent Events within 500ms of state transitions.
