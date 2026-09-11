# Authorization Model (RBAC + ABAC) — Paraxis AI

> **Purpose**: Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) matrix for Paraxis AI.

---

## 1. Role Taxonomy & Access Matrix

| Role | Domain Scope | Permissions |
| :--- | :--- | :--- |
| **`STUDENT`** | Self / Public Campus | `incident:create`, `incident:view_self`, `incident:confirm_resolution`, `attendance:view_self` |
| **`FACULTY`** | Department / Classrooms | `incident:create`, `incident:create_priority`, `attendance:mark_session`, `attendance:view_roster` |
| **`TECHNICIAN`** | Assigned Tasks | `task:view_assigned`, `task:acknowledge`, `task:start`, `task:complete`, `asset:view` |
| **`WARDEN`** | Assigned Hostel / Mess | `hostel:view_queue`, `incident:escalate`, `mess:view_forecast`, `attendance:view_absentees` |
| **`SAFETY_OFFICER`**| Campus Safety | `safety:view_confidential`, `safety:investigate`, `notification:emergency_broadcast` |
| **`CAMPUS_ADMIN`** | Complete Campus | `incident:manage_all`, `task:reassign`, `approval:decide`, `policy:manage`, `audit:view` |
| **`SUPER_ADMIN`** | Organization / Multi-Campus| `tenant:provision`, `campus:manage`, `system:configure`, `audit:export_all` |

---

## 2. Attribute-Based Access Control (ABAC) Rules

In addition to static roles, certain sensitive operations evaluate contextual attributes:
1. **Technician Task Completion**: User must have role `TECHNICIAN` **AND** `task.assigned_to_id == request.user.id` (or user has `CAMPUS_ADMIN`).
2. **Safety Case Access**: User must have role `SAFETY_OFFICER` **AND** `case.assigned_officer_id == request.user.id` (or Chief Security Officer).
3. **Emergency Broadcast**: User must have role `CAMPUS_ADMIN` or `SAFETY_OFFICER` **AND** request must include two-factor authentication or explicit physical confirmation.
