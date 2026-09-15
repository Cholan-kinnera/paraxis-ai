"""
Typed Tool Contracts and Pydantic Schemas for Paraxis AI.
Adheres to ADR-005 and docs/agents/tool-contracts.md.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# 1. get_location_context
class GetLocationContextInput(BaseModel):
    building_name: str
    room_number: str
    campus_id: str


class AssetSummary(BaseModel):
    asset_id: str
    name: str
    tag: str
    status: str


class GetLocationContextOutput(BaseModel):
    building_id: Optional[str] = None
    building_name: str
    room_id: Optional[str] = None
    room_number: str
    floor: Optional[int] = None
    capacity: Optional[int] = None
    assets: List[AssetSummary] = Field(default_factory=list)


# 2. search_related_incidents
class SearchRelatedIncidentsInput(BaseModel):
    query_text: str
    campus_id: str
    building_id: Optional[str] = None
    room_id: Optional[str] = None
    limit: int = 5


class IncidentMatch(BaseModel):
    incident_id: str
    title: str
    status: str
    similarity_score: float
    created_at: str


class SearchRelatedIncidentsOutput(BaseModel):
    matches: List[IncidentMatch] = Field(default_factory=list)


# 3. search_policies
class SearchPoliciesInput(BaseModel):
    category: str
    campus_id: str


class PolicySummary(BaseModel):
    policy_id: str
    title: str
    rules_summary: str
    max_auto_cost: float = 500.0
    approval_role_required: Optional[str] = None


class SearchPoliciesOutput(BaseModel):
    policies: List[PolicySummary] = Field(default_factory=list)


# 4. get_department_capabilities
class GetDepartmentCapabilitiesInput(BaseModel):
    department_id: str
    campus_id: str


class GetDepartmentCapabilitiesOutput(BaseModel):
    department_name: str
    is_open_now: bool = True
    available_staff_count: int = 1
    on_call_supervisor_id: Optional[str] = None


# 5. calculate_priority
class CalculatePriorityInput(BaseModel):
    category: str
    room_type: Optional[str] = None
    student_count_affected: int = 0
    urgency_flag: bool = False


class CalculatePriorityOutput(BaseModel):
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    sla_target_hours: float
    rationale: str


# 6. create_incident_task
class CreateIncidentTaskInput(BaseModel):
    incident_id: str
    department_id: Optional[str] = None
    title: str
    instructions: str = ""
    priority: str = "MEDIUM"
    idempotency_key: Optional[str] = None


class CreateIncidentTaskOutput(BaseModel):
    task_id: str
    status: str
    created_at: str


# 7. assign_task
class AssignTaskInput(BaseModel):
    task_id: str
    assignee_user_id: str
    idempotency_key: Optional[str] = None


class AssignTaskOutput(BaseModel):
    task_id: str
    assignee_name: str
    assigned_at: str


# 8. send_notification
class SendNotificationInput(BaseModel):
    recipient_user_id: str
    title: str
    message: str
    channel: str = "IN_APP"
    priority: str = "NORMAL"


class SendNotificationOutput(BaseModel):
    notification_id: str
    status: str


# 9. request_human_approval
class RequestHumanApprovalInput(BaseModel):
    incident_id: str
    proposed_action: str
    reason: str
    required_role: str
    estimated_cost: float = 0.0


class RequestHumanApprovalOutput(BaseModel):
    approval_id: str
    status: str = "PENDING"


# 10. escalate_incident
class EscalateIncidentInput(BaseModel):
    incident_id: str
    escalation_reason: str


class EscalateIncidentOutput(BaseModel):
    incident_id: str
    escalated_to_id: Optional[str] = None
    escalated_at: str


# 11. record_resolution
class RecordResolutionInput(BaseModel):
    incident_id: str
    resolution_summary: str
    technician_id: Optional[str] = None


class RecordResolutionOutput(BaseModel):
    incident_id: str
    status: str = "RESOLVED"
    resolved_at: str
