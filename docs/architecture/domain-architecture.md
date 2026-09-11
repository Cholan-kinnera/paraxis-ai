# Domain Architecture & Canonical Entity Model — Paraxis AI

> **Purpose**: Definitive canonical domain model for Paraxis AI. Defines entity purposes, ownership, tenant scopes, lifecycles, fields, relationships, invariants, and audit requirements.

---

## 1. Domain Overview & Entity Classification

The domain entities are partitioned into 7 bounded contexts:
1. **Identity & Governance**: `Organization`, `Campus`, `User`, `Role`, `Permission`
2. **Campus Physical Graph**: `Department`, `Building`, `Location`, `Room`, `Asset`
3. **Incident & Remediation Engine**: `Incident`, `IncidentEvent`, `Task`, `SLA`, `Approval`
4. **Safety, Emergency & Trust**: `SafetyCase`, `Notification`
5. **Academic & Attendance Operations**: `ClassSession`, `AttendanceRecord`
6. **Hostel & Mess Operations**: `MealForecast`, `MealOperation`
7. **Intelligence, Audit & Memory**: `OperationalInsight`, `AuditLog`, `AgentRun`, `AgentToolCall`

---

## 2. Canonical Entity Specifications

### 2.1 Organization
- **Purpose**: Top-level institutional entity (e.g., University System, Educational Trust).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: Root entity (No parent tenant).
- **Lifecycle**: `ACTIVE` -> `SUSPENDED` -> `TERMINATED`.
- **Key Fields**: `id (UUID)`, `name (VARCHAR)`, `slug (SLUG)`, `created_at`, `updated_at`.
- **Relationships**: 1:N with `Campus`, 1:N with `User`.
- **Invariants**: Slugs must be globally unique.
- **Authorization**: Super Administrator only.
- **Audit**: All changes logged in `AuditLog`.

### 2.2 Campus
- **Purpose**: Physical or administrative campus branch (e.g., Downtown Campus, Medical Campus).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Organization`.
- **Lifecycle**: `ACTIVE` -> `MAINTENANCE` -> `INACTIVE`.
- **Key Fields**: `id (UUID)`, `organization_id (FK)`, `name`, `code`, `timezone`, `address`, `created_at`.
- **Relationships**: Belongs to `Organization`; 1:N with `Department`, `Building`, `Incident`.
- **Invariants**: `code` unique per Organization.
- **Authorization**: Organization Admin or Super Admin.
- **Audit**: All changes logged.

### 2.3 User
- **Purpose**: Individual campus actor (Student, Faculty, Staff, Warden, Administrator).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: Belongs to `Organization`; assigned to primary `Campus`.
- **Lifecycle**: `PENDING_VERIFICATION` -> `ACTIVE` -> `SUSPENDED` -> `DEACTIVATED`.
- **Key Fields**: `id (UUID)`, `email`, `password_hash`, `full_name`, `phone_number`, `is_active`, `is_staff`.
- **Relationships**: M:N with `Role`, 1:N with `Incident` (as reporter), 1:N with `Task` (as assignee).
- **Invariants**: Email unique per Organization.
- **Authorization**: Self (read/update profile), Campus Admin (manage users).
- **Audit**: Password resets, status changes, and role assignments logged.

### 2.4 Role
- **Purpose**: Named role for RBAC authorization (e.g., `STUDENT`, `FACULTY`, `WARDEN`, `IT_STAFF`, `SAFETY_OFFICER`, `CAMPUS_ADMIN`).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: Organization-level or system-wide.
- **Lifecycle**: `ACTIVE` -> `DEPRECATED`.
- **Key Fields**: `id`, `name`, `description`, `is_system_role`.
- **Relationships**: M:N with `Permission`, M:N with `User`.
- **Invariants**: System roles cannot be deleted.
- **Authorization**: Campus Admin / Super Admin.
- **Audit**: Permission updates logged.

### 2.5 Permission
- **Purpose**: Granular capability string (e.g., `incident:create`, `incident:approve_action`, `safety:view_confidential`).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: System-wide.
- **Lifecycle**: Static system definition.
- **Key Fields**: `id`, `codename`, `name`, `module`.
- **Relationships**: M:N with `Role`.
- **Invariants**: Codenames immutable.
- **Authorization**: Super Admin only.
- **Audit**: System initialization only.

### 2.6 Department
- **Purpose**: Functional operational unit (e.g., IT Services, Facilities & Maintenance, Electrical, Mess Operations).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `ACTIVE` -> `INACTIVE`.
- **Key Fields**: `id`, `campus_id (FK)`, `name`, `code`, `contact_email`, `escalation_contact_id (FK User)`.
- **Relationships**: Belongs to `Campus`; 1:N with `Task`, 1:N with `Asset`.
- **Invariants**: Department code unique per campus.
- **Authorization**: Campus Admin.
- **Audit**: Creation and escalation contact changes logged.

### 2.7 Building
- **Purpose**: Physical campus structure (e.g., Block B, Science Hall, Hostel 3).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `OPERATIONAL` -> `RENOVATION` -> `DECOMMISSIONED`.
- **Key Fields**: `id`, `campus_id (FK)`, `name`, `code`, `floors_count`, `gis_polygon`.
- **Relationships**: Belongs to `Campus`; 1:N with `Room`, 1:N with `Location`.
- **Invariants**: Building code unique per campus.
- **Authorization**: Facility Admin / Campus Admin.
- **Audit**: Structural edits logged.

### 2.8 Location
- **Purpose**: Generalized physical coordinate or named area (e.g., North Courtyard, Mess Entrance).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `ACTIVE` -> `INACTIVE`.
- **Key Fields**: `id`, `campus_id (FK)`, `building_id (FK, optional)`, `name`, `latitude`, `longitude`.
- **Relationships**: Linked to `Building` or standalone campus grounds.
- **Invariants**: Latitude/longitude must be valid GPS coordinates if present.
- **Authorization**: Facility Admin.
- **Audit**: Logged.

### 2.9 Room
- **Purpose**: Granular identifiable indoor space (e.g., Room 204, Chemistry Lab 2).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `AVAILABLE` -> `OCCUPIED` -> `UNDER_MAINTENANCE`.
- **Key Fields**: `id`, `building_id (FK)`, `room_number`, `floor`, `room_type`, `capacity`.
- **Relationships**: Belongs to `Building`; 1:N with `Asset`.
- **Invariants**: Room number unique within Building.
- **Authorization**: Facility Admin.
- **Audit**: Logged.

### 2.10 Asset
- **Purpose**: Maintainable physical equipment (e.g., Wi-Fi Access Point AP-04, AC Compressor 2B, Water Dispenser).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `OPERATIONAL` -> `DEGRADED` -> `OUT_OF_SERVICE` -> `RETIRED`.
- **Key Fields**: `id`, `campus_id (FK)`, `department_id (FK)`, `room_id (FK, optional)`, `name`, `asset_tag`, `category`, `install_date`.
- **Relationships**: Belongs to `Department`, assigned to `Room` or `Building`; 1:N with `Incident`.
- **Invariants**: `asset_tag` unique per campus.
- **Authorization**: Department Staff / Facility Admin.
- **Audit**: Status changes and maintenance history logged.

### 2.11 Incident
- **Purpose**: Core operational event or problem reported by a human or agent.
- **Ownership**: Django Core Platform (state & persistence); FastAPI Intelligence (triaging & enrichment).
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `INGESTED` -> `TRIAGING` -> `PENDING_APPROVAL` -> `ASSIGNED` -> `IN_PROGRESS` -> `ESCALATED` -> `RESOLVED` -> `VERIFIED` -> `CLOSED`.
- **Key Fields**: `id (UUID)`, `campus_id (FK)`, `reporter_id (FK User)`, `title`, `description_raw`, `category`, `priority (LOW/MEDIUM/HIGH/CRITICAL)`, `status`, `building_id (FK)`, `room_id (FK)`, `asset_id (FK)`, `is_duplicate_of_id (FK Self)`.
- **Relationships**: Belongs to `Campus`; 1:N with `IncidentEvent`, 1:N with `Task`, 1:1 with `SLA`.
- **Invariants**: Cannot transition to `RESOLVED` without at least one verified `Task` completion.
- **Authorization**: Create: Any authenticated user; Update: Assigned department staff or admin.
- **Audit**: Every state change produces an `IncidentEvent` and `AuditLog`.

### 2.12 IncidentEvent
- **Purpose**: Immutable chronological event in the incident timeline (e.g., "Reported", "Triaged by Paraxis AI", "Dispatched to IT", "SLA Breached").
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus` (via `Incident`).
- **Lifecycle**: Append-only (Immutable).
- **Key Fields**: `id`, `incident_id (FK)`, `event_type`, `description`, `actor_type (USER/AGENT/SYSTEM)`, `actor_id`, `metadata (JSON)`, `created_at`.
- **Relationships**: Belongs to `Incident`.
- **Invariants**: Once written, cannot be edited or deleted.
- **Authorization**: System and authorized staff.
- **Audit**: Self-auditing append-only table.

### 2.13 Task
- **Purpose**: Unit of work assigned to an individual technician or operational crew.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `CREATED` -> `ASSIGNED` -> `IN_PROGRESS` -> `BLOCKED` -> `COMPLETED` -> `CANCELLED`.
- **Key Fields**: `id`, `incident_id (FK)`, `department_id (FK)`, `assigned_to_id (FK User)`, `title`, `instructions`, `status`, `started_at`, `completed_at`.
- **Relationships**: Belongs to `Incident` and `Department`.
- **Invariants**: `completed_at` must be >= `started_at`.
- **Authorization**: Department staff and task assignee.
- **Audit**: State transitions logged.

### 2.14 SLA
- **Purpose**: Operational service level agreement tracking deadlines for acknowledgment and resolution.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `ACTIVE` -> `MET` -> `BREACHED` -> `PAUSED`.
- **Key Fields**: `id`, `incident_id (FK)`, `ack_deadline`, `ack_time`, `resolution_deadline`, `resolution_time`, `status`.
- **Relationships**: 1:1 with `Incident`.
- **Invariants**: Deadlines calculated deterministically from incident priority and campus policy.
- **Authorization**: System automated calculation; Admin override.
- **Audit**: Breaches trigger automatic escalation events.

### 2.15 Approval
- **Purpose**: Formal human sign-off request generated when an action triggers a policy condition.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `PENDING` -> `APPROVED` -> `REJECTED` -> `EXPIRED`.
- **Key Fields**: `id`, `incident_id (FK)`, `agent_run_id (UUID)`, `required_role`, `approver_id (FK User)`, `action_payload (JSON)`, `decision_notes`, `decided_at`.
- **Relationships**: Belongs to `Incident`.
- **Invariants**: Approved action can only be executed once.
- **Authorization**: User with matching `required_role`.
- **Audit**: All decisions strictly recorded with actor ID, timestamp, and justification.

### 2.16 Notification
- **Purpose**: Outbound user communication dispatch (Push, Email, In-App).
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `QUEUED` -> `SENT` -> `DELIVERED` -> `FAILED`.
- **Key Fields**: `id`, `recipient_id (FK User)`, `channel (IN_APP/EMAIL/PUSH)`, `title`, `body`, `status`, `sent_at`.
- **Relationships**: Belongs to `User`.
- **Invariants**: Notifications must adhere to campus quiet hours policies unless flagged `EMERGENCY`.
- **Authorization**: System generated.
- **Audit**: Logged.

### 2.17 SafetyCase
- **Purpose**: Encrypted, highly confidential reporting container for harassment, mental health, or critical security threats.
- **Ownership**: Django Core Platform (Dedicated secure domain).
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `FILED` -> `INVESTIGATING` -> `ACTION_TAKEN` -> `CLOSED`.
- **Key Fields**: `id`, `campus_id (FK)`, `case_number`, `reporter_id (FK User, Nullable for Anonymous)`, `encrypted_details`, `severity`, `assigned_officer_id (FK User)`.
- **Relationships**: Belongs to `Campus`.
- **Invariants**: Access restricted exclusively to verified `SAFETY_OFFICER` roles. Reporter identity masked.
- **Authorization**: Safety Officer only.
- **Audit**: Access to safety case details is strictly logged in `AuditLog` on every read.

### 2.18 ClassSession
- **Purpose**: Scheduled academic class or lecture instance.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `SCHEDULED` -> `IN_SESSION` -> `CONCLUDED` -> `CANCELLED`.
- **Key Fields**: `id`, `campus_id (FK)`, `course_code`, `instructor_id (FK User)`, `room_id (FK Room)`, `start_time`, `end_time`.
- **Relationships**: Belongs to `Campus` and `Room`.
- **Invariants**: `start_time` < `end_time`.
- **Authorization**: Faculty and Academic Admin.
- **Audit**: Class cancellations logged.

### 2.19 AttendanceRecord
- **Purpose**: Individual student presence status for a given `ClassSession`.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `RECORDED` -> `DISPUTED` -> `CORRECTED`.
- **Key Fields**: `id`, `session_id (FK ClassSession)`, `student_id (FK User)`, `status (PRESENT/ABSENT/EXCUSED/LATE)`, `marked_by_id (FK User)`, `timestamp`.
- **Relationships**: Belongs to `ClassSession` and `User`.
- **Invariants**: One record per student per session.
- **Authorization**: Instructor / Academic Admin.
- **Audit**: Manual attendance overrides logged with justification.

### 2.20 MealForecast
- **Purpose**: Predictive daily dining hall headcounts to minimize mess food waste.
- **Ownership**: Django Core Platform (persisted); FastAPI Intelligence (model prediction).
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `DRAFT` -> `PUBLISHED` -> `RECONCILED`.
- **Key Fields**: `id`, `campus_id (FK)`, `mess_facility_name`, `target_date`, `meal_type (BREAKFAST/LUNCH/DINNER)`, `projected_count`, `actual_count`, `variance_percentage`.
- **Relationships**: Belongs to `Campus`.
- **Invariants**: Projected counts must be positive integers.
- **Authorization**: Mess Manager.
- **Audit**: Logged.

### 2.21 MealOperation
- **Purpose**: Operational mess log recording food production, wastage, and student satisfaction.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `LOGGED`.
- **Key Fields**: `id`, `forecast_id (FK MealForecast)`, `food_wasted_kg`, `cost_per_plate`, `student_rating_avg`, `notes`.
- **Relationships**: Belongs to `MealForecast`.
- **Invariants**: Wasted kilograms >= 0.
- **Authorization**: Mess Staff.
- **Audit**: Logged.

### 2.22 OperationalInsight
- **Purpose**: Long-term operational pattern, recurring failure mode, or anomaly discovered by operational memory analysis.
- **Ownership**: Django Core Platform (persisted); FastAPI Intelligence (analysis).
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `DETECTED` -> `REVIEWED` -> `ACTIONED` -> `DISMISSED`.
- **Key Fields**: `id`, `campus_id (FK)`, `title`, `insight_type (RECURRING_FAILURE/SLA_BOTTLENECK/ANOMALY)`, `evidence_json`, `recommendation`, `confidence_score (0.0 - 1.0)`, `detected_at`.
- **Relationships**: Belongs to `Campus`; references `Asset`, `Building`, or `Department`.
- **Invariants**: Must include clear distinction between FACT and INFERENCE.
- **Authorization**: Campus Admin / Operations Director.
- **Audit**: Status changes logged.

### 2.23 AuditLog
- **Purpose**: Central immutable audit trail for all business state mutations and administrative actions.
- **Ownership**: Django Core Platform.
- **Tenant Scope**: `Organization` & `Campus`.
- **Lifecycle**: Append-only (Strictly Immutable).
- **Key Fields**: `id (BIGINT/UUID)`, `organization_id`, `campus_id`, `actor_id`, `actor_type`, `ip_address`, `action`, `entity_type`, `entity_id`, `pre_state_json`, `post_state_json`, `created_at`.
- **Relationships**: References entity identifiers.
- **Invariants**: Append-only; no UPDATE or DELETE queries permitted on this table.
- **Authorization**: Read-only by authorized Compliance/Super Admin.
- **Audit**: Self-contained.

### 2.24 AgentRun
- **Purpose**: Persistent telemetry record of a single LangGraph agent execution session.
- **Ownership**: FastAPI Intelligence (telemetry dispatch) & Django Core (persistence).
- **Tenant Scope**: `Campus`.
- **Lifecycle**: `STARTED` -> `RUNNING` -> `PAUSED_FOR_APPROVAL` -> `COMPLETED` -> `FAILED`.
- **Key Fields**: `id (UUID)`, `incident_id (FK)`, `agent_name`, `model_name`, `prompt_tokens`, `completion_tokens`, `total_latency_ms`, `final_status`, `error_message`, `created_at`.
- **Relationships**: Belongs to `Incident`; 1:N with `AgentToolCall`.
- **Invariants**: Token counts and latency must be non-negative.
- **Authorization**: System recorded; visible to Operations Admin.
- **Audit**: Captured per execution.

### 2.25 AgentToolCall
- **Purpose**: Granular execution record of an individual tool invocation by an agent.
- **Ownership**: FastAPI Intelligence (telemetry dispatch) & Django Core (persistence).
- **Tenant Scope**: `Campus` (via `AgentRun`).
- **Lifecycle**: `PROPOSED` -> `EVALUATED` -> `EXECUTED` -> `FAILED`.
- **Key Fields**: `id (UUID)`, `agent_run_id (FK)`, `tool_name`, `input_parameters (JSON)`, `policy_decision (ALLOW/DENY/APPROVAL)`, `policy_reason`, `output_payload (JSON)`, `latency_ms`, `created_at`.
- **Relationships**: Belongs to `AgentRun`.
- **Invariants**: `output_payload` must conform to the tool's registered output schema.
- **Authorization**: System recorded.
- **Audit**: Logged.
