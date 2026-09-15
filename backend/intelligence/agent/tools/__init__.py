"""
Typed Tool Registry and Contracts for Paraxis AI.
"""
from backend.intelligence.agent.tools.schemas import (
    GetLocationContextInput, GetLocationContextOutput,
    SearchRelatedIncidentsInput, SearchRelatedIncidentsOutput,
    SearchPoliciesInput, SearchPoliciesOutput,
    GetDepartmentCapabilitiesInput, GetDepartmentCapabilitiesOutput,
    CalculatePriorityInput, CalculatePriorityOutput,
    CreateIncidentTaskInput, CreateIncidentTaskOutput,
    AssignTaskInput, AssignTaskOutput,
    SendNotificationInput, SendNotificationOutput,
    RequestHumanApprovalInput, RequestHumanApprovalOutput,
    EscalateIncidentInput, EscalateIncidentOutput,
    RecordResolutionInput, RecordResolutionOutput,
)
from backend.intelligence.agent.tools.client import DjangoCoreClient
from backend.intelligence.agent.tools.registry import ToolRegistry, ToolDefinition, get_tool_registry

__all__ = [
    "DjangoCoreClient",
    "ToolRegistry",
    "ToolDefinition",
    "get_tool_registry",
    "GetLocationContextInput", "GetLocationContextOutput",
    "SearchRelatedIncidentsInput", "SearchRelatedIncidentsOutput",
    "SearchPoliciesInput", "SearchPoliciesOutput",
    "GetDepartmentCapabilitiesInput", "GetDepartmentCapabilitiesOutput",
    "CalculatePriorityInput", "CalculatePriorityOutput",
    "CreateIncidentTaskInput", "CreateIncidentTaskOutput",
    "AssignTaskInput", "AssignTaskOutput",
    "SendNotificationInput", "SendNotificationOutput",
    "RequestHumanApprovalInput", "RequestHumanApprovalOutput",
    "EscalateIncidentInput", "EscalateIncidentOutput",
    "RecordResolutionInput", "RecordResolutionOutput",
]
