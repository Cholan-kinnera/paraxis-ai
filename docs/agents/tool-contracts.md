# Typed Tool Contracts — Paraxis AI

> **Purpose**: Definitive specification for all 11 registered agent tools. Prohibits arbitrary SQL, shell, or HTTP execution.

---

## 1. Tool Governance Principles

1. **Strict Typing**: All inputs and outputs must adhere to typed Pydantic models.
2. **Deterministic Side Effects**: Read-only tools execute synchronously; write tools mutate state exclusively via Django Core's internal service APIs.
3. **Idempotency**: All mutation tools accept an `idempotency_key` (derived from `agent_run_id + step_index`).
4. **Audit Logging**: Every invocation produces an `AgentToolCall` audit record.

---

## 2. Tool Specifications

### 2.1 `get_location_context`
- **Description**: Resolves building name and room number to canonical database identifiers, active assets, and current occupancy.
- **Input Schema**: `{ building_name: str, room_number: str, campus_id: str }`
- **Output Schema**: `{ building_id: str, room_id: str, floor: int, capacity: int, assets: List[{ asset_id: str, name: str, tag: str, status: str }] }`
- **Permissions**: `campus:read_graph`
- **Allowed Actors**: `AGENT`, `STAFF`
- **Side Effects**: None (Read-only).
- **Idempotency**: Naturally idempotent.
- **Audit**: Logged in `AgentToolCall`.
- **Failure Behavior**: Returns empty asset list if room not found; does not throw exception.

### 2.2 `search_related_incidents`
- **Description**: Performs hybrid vector and spatial search for open incidents in the same room or building within the last 48 hours.
- **Input Schema**: `{ query_text: str, campus_id: str, building_id: Optional[str], room_id: Optional[str], limit: int = 5 }`
- **Output Schema**: `{ matches: List[{ incident_id: str, title: str, status: str, similarity_score: float, created_at: str }] }`
- **Permissions**: `incident:read`
- **Allowed Actors**: `AGENT`, `STAFF`
- **Side Effects**: None (Read-only).
- **Idempotency**: Naturally idempotent.
- **Audit**: Logged.
- **Failure Behavior**: Returns empty match list on search error.

### 2.3 `search_policies`
- **Description**: Retrieves approved campus operational policies and standard operating procedures matching the incident category.
- **Input Schema**: `{ category: str, campus_id: str }`
- **Output Schema**: `{ policies: List[{ policy_id: str, title: str, rules_summary: str, max_auto_cost: float, approval_role_required: Optional[str] }] }`
- **Permissions**: `policy:read`
- **Allowed Actors**: `AGENT`
- **Side Effects**: None.
- **Idempotency**: Naturally idempotent.
- **Audit**: Logged.
- **Failure Behavior**: Returns default campus baseline policy if category unmatched.

### 2.4 `get_department_capabilities`
- **Description**: Returns department operational hours, current technician availability, and escalation contact.
- **Input Schema**: `{ department_id: str, campus_id: str }`
- **Output Schema**: `{ department_name: str, is_open_now: bool, available_staff_count: int, on_call_supervisor_id: str }`
- **Permissions**: `department:read`
- **Allowed Actors**: `AGENT`, `STAFF`
- **Side Effects**: None.
- **Idempotency**: Naturally idempotent.
- **Audit**: Logged.
- **Failure Behavior**: Flags department as offline if outside operating hours.

### 2.5 `calculate_priority`
- **Description**: Deterministically evaluates room importance, blast radius, and report urgency to compute operational priority.
- **Input Schema**: `{ category: str, room_type: str, student_count_affected: int, urgency_flag: bool }`
- **Output Schema**: `{ priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"], sla_target_hours: float, rationale: str }`
- **Permissions**: Internal calculation.
- **Allowed Actors**: `AGENT`
- **Side Effects**: None.
- **Idempotency**: Pure function; deterministic.
- **Audit**: Calculation rationale recorded in state.
- **Failure Behavior**: Defaults to `MEDIUM` priority on ambiguous parameters.

### 2.6 `create_incident_task`
- **Description**: Creates a persistent work order in Django Core linked to the incident and responsible department.
- **Input Schema**: `{ incident_id: str, department_id: str, title: str, instructions: str, priority: str, idempotency_key: str }`
- **Output Schema**: `{ task_id: str, status: str, created_at: str }`
- **Permissions**: `task:create`
- **Allowed Actors**: `AGENT`, `STAFF`
- **Side Effects**: Inserts row into `tasks` table; publishes Redis event.
- **Idempotency**: Deduped via `idempotency_key`.
- **Audit**: Produces `AuditLog` entry in Django Core.
- **Failure Behavior**: Transactional rollback; returns error envelope.

### 2.7 `assign_task`
- **Description**: Assigns a pending task to an available technician.
- **Input Schema**: `{ task_id: str, assignee_user_id: str, idempotency_key: str }`
- **Output Schema**: `{ task_id: str, assignee_name: str, assigned_at: str }`
- **Permissions**: `task:assign`
- **Allowed Actors**: `AGENT`, `DISPATCHER`
- **Side Effects**: Updates `tasks.assigned_to_id`; triggers notification to technician.
- **Idempotency**: Idempotent update.
- **Audit**: Logged in `AuditLog`.
- **Failure Behavior**: Fails if user is inactive or belongs to a different campus.

### 2.8 `send_notification`
- **Description**: Enqueues an in-app or push notification to a student or staff member.
- **Input Schema**: `{ recipient_user_id: str, title: str, message: str, channel: str, priority: str }`
- **Output Schema**: `{ notification_id: str, status: str }`
- **Permissions**: `notification:send`
- **Allowed Actors**: `AGENT`, `SYSTEM`
- **Side Effects**: Enqueues notification; enforces quiet-hours policy.
- **Idempotency**: Rate-limited per recipient/incident.
- **Audit**: Logged in `notifications`.
- **Failure Behavior**: Degrades gracefully; delivery failure does not halt the agent workflow.

### 2.9 `request_human_approval`
- **Description**: Halts the workflow and posts an interactive approval requirement to the Command Center.
- **Input Schema**: `{ incident_id: str, proposed_action: str, reason: str, required_role: str, estimated_cost: float }`
- **Output Schema**: `{ approval_id: str, status: "PENDING" }`
- **Permissions**: `approval:request`
- **Allowed Actors**: `AGENT`
- **Side Effects**: Inserts into `approvals`; suspends LangGraph execution.
- **Idempotency**: One active approval request per incident action.
- **Audit**: Strictly logged in `approvals` and `AuditLog`.
- **Failure Behavior**: Incident remains paused until human intervention.

### 2.10 `escalate_incident`
- **Description**: Flags an incident as breached/escalated and alerts the department supervisor.
- **Input Schema**: `{ incident_id: str, escalation_reason: str }`
- **Output Schema**: `{ incident_id: str, escalated_to_id: str, escalated_at: str }`
- **Permissions**: `incident:escalate`
- **Allowed Actors**: `AGENT`, `SLA_MONITOR`, `STAFF`
- **Side Effects**: Updates incident status to `ESCALATED`; publishes emergency notification.
- **Idempotency**: Idempotent transition.
- **Audit**: Recorded in `IncidentEvent` and `AuditLog`.
- **Failure Behavior**: Alerts campus admin if supervisor contact is missing.

### 2.11 `record_resolution`
- **Description**: Records verified completion of physical repairs with technician notes.
- **Input Schema**: `{ incident_id: str, resolution_summary: str, technician_id: str }`
- **Output Schema**: `{ incident_id: str, status: "RESOLVED", resolved_at: str }`
- **Permissions**: `incident:resolve`
- **Allowed Actors**: `STAFF`, `DISPATCHER`
- **Side Effects**: Updates `incidents.status` to `RESOLVED`; triggers verification prompt to reporter.
- **Idempotency**: Re-resolving an already resolved incident returns current record.
- **Audit**: Logged.
- **Failure Behavior**: Transaction rolls back if linked tasks are incomplete.
