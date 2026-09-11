# Security Incident Response Protocol — Paraxis AI

> **Purpose**: Protocol for identifying, containing, mitigating, and documenting cybersecurity and operational safety breaches within Paraxis AI.

---

## 1. Incident Severity Levels

- **SEV-1 (Critical)**: Active cross-tenant data breach, prompt injection causing unauthorized financial dispatch, uncontained database credential leak.
- **SEV-2 (High)**: Denial of service impacting campus incident reporting, failure of Policy Engine gating, authentication outage.
- **SEV-3 (Medium)**: Intermittent SSE streaming failures, single-tenant UI disruption, minor role authorization defect.
- **SEV-4 (Low)**: Cosmetic UI issue, non-security logging anomaly.

---

## 2. Response Workflow

1. **Detection & Triage (T + 15m)**: Incident flagged via automated alerts, staff report, or security disclosure. Incident Commander assigned.
2. **Containment (T + 30m)**:
   - For prompt injection or agent misbehavior: **Emergency Kill Switch** activated via feature flag (`ENABLE_AGENT_AUTONOMOUS_DISPATCH=false`), forcing 100% of actions to manual staff approval.
   - For compromised credential: Rotate database credentials and revoke active JWT signing keys immediately.
3. **Remediation & Patching (T + 4h)**: Deploy hotfix via CI/CD pipeline with regression tests.
4. **Post-Mortem & Disclosure (T + 48h)**: Publish blameless post-mortem identifying root cause, impacted records, and preventive structural changes.
