# MVP Scope & Boundaries — Paraxis AI

> **Purpose**: Explicit boundaries defining what is strictly IN-SCOPE vs. OUT-OF-SCOPE for the initial Paraxis AI MVP.

---

## 1. In-Scope for MVP

The MVP delivers a complete, production-grade vertical slice of **AI Campus Issue & Maintenance**:
1. **Reporting Experience**:
   - Single clean web view for students/faculty to report issues in conversational natural language.
2. **AI Reasoning & Contextualization Engine**:
   - Extraction of entity triplets: `[Action, Location/Asset, Urgency]`.
   - Campus Graph matching: Resolves `"Block B, Room 204"` to exact room entity and associated `AP-04` access point.
   - Vector similarity duplicate detection: Matches subsequent reports to active master incidents.
3. **Deterministic Policy Gate**:
   - Gating mechanism with standard campus rules.
   - Triggers `REQUIRE_HUMAN_APPROVAL` on high-cost or safety-critical actions.
4. **Command Center UI**:
   - Live streaming incident queue via Server-Sent Events (SSE).
   - Agent evidence panel displaying extracted context, confidence, and policy decisions.
   - Technician dispatch and task acknowledgment flow.
5. **Operational Memory Demonstration**:
   - Mining historical incidents in Block B to surface recurring AP-04 failure patterns.

---

## 2. Explicitly Out-of-Scope for MVP

To ensure depth, reliability, and architectural excellence, the following items are deferred:
- ❌ Complete ERP fee collection and academic gradebook features.
- ❌ Complex biometric IoT hardware integrations.
- ❌ Native iOS/Android app store deployments (responsive web app used for MVP).
- ❌ Enterprise SAML/SCIM SSO (standard JWT email/password auth used for MVP).
- ❌ Live WhatsApp Twilio integration (mocked notification bus used for MVP).
