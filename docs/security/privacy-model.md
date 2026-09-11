# Privacy & Data Minimization Model — Paraxis AI

> **Purpose**: Student privacy protections, confidential whistleblower masking, and data retention policies for Paraxis AI.

---

## 1. Student Privacy & Data Minimization

1. **Least-Privilege Visibility**: Routine maintenance workers dispatched to fix an asset see only the location, asset tag, and issue description—they do **not** receive the student's full academic profile, GPA, or personal phone number.
2. **Confidential Safety Case Masking**:
   - For sensitive harassment or mental health reports, the reporter's user ID is masked with a cryptographic hash.
   - Only authorized `SAFETY_OFFICER` roles can access encrypted case notes.
3. **AI Provider Data Privacy**:
   - Model gateway zero-data-retention agreements: We instruct upstream AI providers (Google, OpenAI) not to retain or train on institutional prompts.
   - PII Scrubbing: Phone numbers and student roll numbers are redacted from prompts sent to third-party model endpoints unless strictly necessary for local context resolution.

---

## 2. Data Retention & Archival Policies

- **Active Operational Incidents**: Retained in active PostgreSQL storage for 1 academic year.
- **Historical Operational Memory**: Aggregated into anonymized failure vectors; raw personal reporter identifiers are stripped after 180 days.
- **Audit Logs**: Retained in immutable storage for a minimum of 3 years to comply with university governance standards.
