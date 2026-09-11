# Paraxis AI Security Policy

Security and data isolation are core engineering tenets of Paraxis AI. Because our platform coordinates physical campus operations, student welfare, safety reporting, and facility maintenance, security controls are built into every architectural layer.

---

## 1. Security Invariants & Defense-in-Depth

### 1.1 Tenant Isolation
- **Strict Partitioning**: Every campus entity is strictly segregated under an `Organization -> Campus` boundary.
- **No Client Trust**: Tenant context is resolved strictly from cryptographically signed JWT credentials issued by Django Core. Client-supplied tenant IDs in route paths or payload bodies are never trusted.
- **ORM & Vector Query Enforcement**: All database operations and vector similarity queries MUST include explicit tenant scope filters.

### 1.2 Authentication & Authorization (RBAC + ABAC)
- All public endpoints require signed, short-lived JWT access tokens with rotating refresh tokens.
- Internal service-to-service communication (e.g., FastAPI calling Django internal endpoints) requires mutual service tokens (`X-Internal-Service-Key`) verified over secure internal networks.
- Authorization enforces least-privilege role-based access control (Student, Faculty, Staff, Warden, Safety Officer, Campus Admin, Super Admin).

### 1.3 AI Threat Model & Tool Safety
- **Untrusted Input Guarantee**: All natural-language user inputs, student reports, and retrieved RAG documents are treated as untrusted text.
- **Prompt Injection Defense**: Untrusted content is quarantined in data fields separated from system instructions. Agents operate with strict tool schemas.
- **No Raw Capabilities**: Agents have NO access to raw SQL, shell execution, unrestricted HTTP egress, or arbitrary file system writes.
- **Deterministic Policy Engine**: Consequential actions (dispatches, work orders, disciplinary flags, public notices) are gated by an independent policy engine and cannot be executed solely on LLM assertion.

### 1.4 SSRF & Network Protections
- All outbound HTTP requests initiated by the platform (e.g., webhook notifications) must pass through a strict URL allowlist with private IP range blocking (RFC 1918 / RFC 3927 metadata ranges blocked).

### 1.5 Sensitive Safety Cases & Data Minimization
- Harassment, mental health, and whistleblower reports in the **Safety, Emergency & Trust** pillar are segregated into an encrypted, strictly restricted domain (`SafetyCase`).
- Identity of confidential reporters is masked at the database level and never exposed in general operational timelines or LLM prompts.

### 1.6 Audit Integrity
- All state mutations, approval decisions, incident state transitions, and agent tool executions are permanently recorded in an append-only `AuditLog` table with user, timestamp, IP, and cryptographic checksum.

---

## 2. Reporting a Security Vulnerability

If you discover a security vulnerability or potential threat in Paraxis AI:
1. **Do NOT disclose publicly**: Do not create public GitHub issues or forum posts.
2. **Contact the Security Team**: Email `security@paraxis.ai` (or the hackathon engineering leads) with:
   - Description of the vulnerability
   - Steps to reproduce / proof of concept
   - Potential impact
   - Suggested remediation
3. **Response Commitment**: We acknowledge receipt of security reports within 24 hours and aim to triage and remediate critical vulnerabilities within 48 hours.
