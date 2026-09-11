# Enterprise Roadmap — Paraxis AI

> **Purpose**: Multi-phase trajectory from hackathon prototype to institutional enterprise SaaS deployment.

---

## 1. Phase Overview & Milestones

```
+------------------+     +------------------+     +------------------+     +------------------+
|  HACKATHON MVP   |     |    PHASE 1 (V1)  |     |   PHASE 2 (V2)   |     |    ENTERPRISE    |
| - Vertical Slice | --> | - Multi-Pillar   | --> | - Advanced Auto  | --> | - Institutional  |
| - Wi-Fi Outage   |     | - Attendance &   |     | - Predictive ML  |     | - Consortium SSO |
| - Policy Gate    |     |   Mess Modules   |     | - Native Mobile  |     | - ERP Connectors |
| - Live Dashboard |     | - Safety Case    |     | - Voice/WhatsApp |     | - SOC2 & Compliance|
+------------------+     +------------------+     +------------------+     +------------------+
```

---

## 2. Detailed Milestone Specifications

### 2.1 Hackathon MVP (Current Focus)
- **Primary Goal**: Flawless execution of the North-Star demo:
  `Natural Language Report -> Triage -> Contextualize -> Duplicate Detect -> Policy Check -> Task Dispatch -> SLA -> Resolution -> Operational Memory`.
- **Infrastructure**: Monorepo with Docker Compose (PostgreSQL 16 + pgvector, Redis 7).
- **Frontend**: Next.js 14 App Router, Tailwind CSS, shadcn/ui.

### 2.2 Phase 1: V1 Core Expansion (Months 1–3)
- **Attendance & Communication Module**: Daily class session roster synchronization, absent student notifications, warden escalations.
- **Hostel & Mess Module**: Kitchen food waste logging, baseline daily meal attendance forecasting.
- **Safety & Trust**: Encrypted safety cases, whistleblower reporter identity masking.
- **Email & SMS Gateway**: Ingestion via support inboxes and SMS emergency broadcasting.

### 2.3 Phase 2: V2 Advanced Automation (Months 4–6)
- **WhatsApp Ingestion**: Conversational issue reporting via official WhatsApp Business API.
- **Predictive Asset Maintenance**: Time-series analysis of asset failures to forecast AC/generator breakdowns.
- **Native Mobile Apps**: Cross-platform iOS and Android technician and student apps built on React Native.
- **Dynamic Policy Rules Builder**: No-code UI for campus facility directors to define custom approval thresholds and dispatch rules.

### 2.4 Enterprise & Institutional Scale (Months 7–12)
- **Identity & Compliance**:
  - SAML 2.0 / Okta / Microsoft Azure AD SSO integration.
  - SCIM 2.0 automatic user provisioning and deprovisioning.
  - SOC 2 Type II compliance audit readiness and data retention automation.
- **Enterprise Integrations**:
  - Pre-built connectors for Ellucian Banner, SAP PM, and Oracle Campus Solutions.
- **Consortium Multi-Tenancy**:
  - Hierarchical governance enabling a state university system to oversee 12 independent physical campuses from a single pane of glass.
