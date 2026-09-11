# Feature Map & Capability Matrix — Paraxis AI

> **Purpose**: Global feature breakdown across product pillars, mapped to maturity levels (Hackathon MVP, V1, V2, Enterprise).

---

## 1. Feature Breakdown by Product Pillar

| Product Pillar | Feature Capability | Description | Target Phase |
| :--- | :--- | :--- | :--- |
| **Campus Issue & Maintenance** | Natural-Language Ingestion | Ingest messy student reports; extract building, room, asset, urgency. | **Hackathon MVP** |
| | Physical Graph Contextualization | Link report to canonical Room, Building, Asset (AP, AC, Breaker). | **Hackathon MVP** |
| | Semantic Duplicate Clustering | Cluster multi-student reports into a single master incident. | **Hackathon MVP** |
| | Deterministic Policy Gate | Evaluate actions (ALLOW, DENY, REQUIRE_HUMAN_APPROVAL). | **Hackathon MVP** |
| | Automated Task Dispatch | Assign work order to responsible department and technician. | **Hackathon MVP** |
| | Live SLA Tracking | Active acknowledgment & resolution timers with escalation. | **Hackathon MVP** |
| | Verification & Feedback Loop | Reporter confirms physical fix before final closure. | **Hackathon MVP** |
| | Operational Memory & Patterns | Cluster historical incidents to detect recurring equipment failure. | **Hackathon MVP** |
| | Predictive Asset Maintenance | ML forecasting of asset failure based on telemetry and age. | Enterprise (V2) |
| **Attendance & Communication** | Class Session Management | Schedule and record daily lecture sessions and rosters. | Phase 1 (Post-Hack) |
| | Attendance Anomaly Detection | Flag abnormal drops in student attendance across cohorts. | Phase 2 (V1) |
| | Automated Warden Alerting | Notify hostel wardens when residential students miss 2+ classes. | Phase 2 (V1) |
| **Hostel & Mess Operations** | Dining Headcount Forecasting | Predict meal attendance based on weekday, exam schedules, holidays. | Phase 3 (V1) |
| | Mess Wastage Reconciliation | Track daily kitchen food waste vs. predicted prep amounts. | Phase 3 (V1) |
| | Menu Satisfaction Sentiment | Student sentiment analysis on dining hall meals. | Phase 4 (V2) |
| **Safety, Emergency & Trust** | Confidential Safety Reporting | Encrypted reporting container with reporter identity masking. | Phase 2 (V1) |
| | Emergency Broadcast Dispatch | Instant SMS/Push broadcast to campus community for critical alerts. | Phase 3 (V1) |
| | Campus SafeWalk Coordination | Student-to-security companion dispatch for late-night transit. | Enterprise (V2) |

---

## 2. Command Center & Administration

| Module | Feature | Target Phase |
| :--- | :--- | :--- |
| **Command Center** | Live Operational Map & Incident List | **Hackathon MVP** |
| | Agent Decision & Evidence Cards | **Hackathon MVP** |
| | Human Approval Interactive Drawer | **Hackathon MVP** |
| | Historical Pattern Insights Widget | **Hackathon MVP** |
| **Administration** | Multi-Campus Tenant Provisioning | Enterprise |
| | SCIM / SAML SSO Integration | Enterprise |
| | Custom Rule Policy Builder | Enterprise |
