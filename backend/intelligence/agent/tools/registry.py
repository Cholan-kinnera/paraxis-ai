"""
Tool Registry for Paraxis AI.
Manages registration, Pydantic validation, and execution of typed tools.
Adheres to ADR-005 and docs/agents/tool-contracts.md.
"""
import time
import uuid
import logging
from typing import Dict, Any, Callable, Optional, List, Type
from pydantic import BaseModel, ValidationError

from backend.intelligence.agent.state import ToolExecutionRecord
from backend.intelligence.agent.tools.client import DjangoCoreClient
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

logger = logging.getLogger("paraxis.tools.registry")


class ToolDefinition:
    """Encapsulates a typed tool registration."""
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        handler: Callable[..., Any],
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.handler = handler

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema.model_json_schema(),
            "returns": self.output_schema.model_json_schema(),
        }


class ToolRegistry:
    """Registry managing all typed tool contracts and their execution."""

    def __init__(self, core_client: Optional[DjangoCoreClient] = None):
        self.client = core_client or DjangoCoreClient()
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(
        self,
        name: str,
        description: str,
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        handler: Callable[..., Any],
    ) -> None:
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            handler=handler,
        )

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self._tools.values()]

    def _register_default_tools(self) -> None:
        # 1. get_location_context
        async def _exec_get_location_context(params: GetLocationContextInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.get_location_context(
                building_name=params.building_name,
                room_number=params.room_number,
                campus_id=params.campus_id,
                correlation_headers=corrs,
            )
            return GetLocationContextOutput(**res).model_dump()

        self.register(
            name="get_location_context",
            description="Query building, floor, room, and connected IoT assets from Campus Graph.",
            input_schema=GetLocationContextInput,
            output_schema=GetLocationContextOutput,
            handler=_exec_get_location_context,
        )

        # 2. search_related_incidents
        async def _exec_search_related(params: SearchRelatedIncidentsInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            matches = await self.client.search_related_incidents(
                query_text=params.query_text,
                campus_id=params.campus_id,
                building_id=params.building_id,
                room_id=params.room_id,
                correlation_headers=corrs,
            )
            return SearchRelatedIncidentsOutput(matches=matches).model_dump()

        self.register(
            name="search_related_incidents",
            description="Search historical and active incidents to detect duplicates and systemic issues.",
            input_schema=SearchRelatedIncidentsInput,
            output_schema=SearchRelatedIncidentsOutput,
            handler=_exec_search_related,
        )

        # 3. search_policies
        async def _exec_search_policies(params: SearchPoliciesInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            policies = await self.client.search_policies(
                category=params.category,
                campus_id=params.campus_id,
                correlation_headers=corrs,
            )
            return SearchPoliciesOutput(policies=policies).model_dump()

        self.register(
            name="search_policies",
            description="Retrieve operating policies, approval limits, and standard protocols.",
            input_schema=SearchPoliciesInput,
            output_schema=SearchPoliciesOutput,
            handler=_exec_search_policies,
        )

        # 4. get_department_capabilities
        async def _exec_get_dept_caps(params: GetDepartmentCapabilitiesInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.get_department_capabilities(
                department_id=params.department_id,
                campus_id=params.campus_id,
                correlation_headers=corrs,
            )
            return GetDepartmentCapabilitiesOutput(**res).model_dump()

        self.register(
            name="get_department_capabilities",
            description="Check department shift hours, technician availability, and on-call supervisor.",
            input_schema=GetDepartmentCapabilitiesInput,
            output_schema=GetDepartmentCapabilitiesOutput,
            handler=_exec_get_dept_caps,
        )

        # 5. calculate_priority
        async def _exec_calc_priority(params: CalculatePriorityInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            # Deterministic priority calculation based on category and impact
            cat = params.category.upper()
            if cat in ["SAFETY", "EMERGENCY"] or params.urgency_flag or params.student_count_affected >= 50:
                p = "CRITICAL"
                sla = 1.0
                rationale = "High impact safety or large audience affected"
            elif cat in ["FACILITIES", "IT"] and (params.student_count_affected > 10 or "LAB" in (params.room_type or "").upper()):
                p = "HIGH"
                sla = 4.0
                rationale = "Affects critical academic/lab operations"
            elif cat in ["FACILITIES", "IT"]:
                p = "MEDIUM"
                sla = 8.0
                rationale = "Standard maintenance ticket"
            else:
                p = "LOW"
                sla = 24.0
                rationale = "Routine inquiry or non-disruptive issue"

            return CalculatePriorityOutput(priority=p, sla_target_hours=sla, rationale=rationale).model_dump()

        self.register(
            name="calculate_priority",
            description="Deterministic evaluation of priority and SLA target based on campus operational rules.",
            input_schema=CalculatePriorityInput,
            output_schema=CalculatePriorityOutput,
            handler=_exec_calc_priority,
        )

        # 6. create_incident_task
        async def _exec_create_task(params: CreateIncidentTaskInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.create_task(
                incident_id=params.incident_id,
                title=params.title,
                instructions=params.instructions,
                priority=params.priority,
                department_id=params.department_id,
                idempotency_key=params.idempotency_key,
                correlation_headers=corrs,
            )
            return CreateIncidentTaskOutput(**res).model_dump()

        self.register(
            name="create_incident_task",
            description="Create an operational Task linked to an Incident in Django Core.",
            input_schema=CreateIncidentTaskInput,
            output_schema=CreateIncidentTaskOutput,
            handler=_exec_create_task,
        )

        # 7. assign_task
        async def _exec_assign_task(params: AssignTaskInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.assign_task(
                task_id=params.task_id,
                assignee_user_id=params.assignee_user_id,
                idempotency_key=params.idempotency_key,
                correlation_headers=corrs,
            )
            return AssignTaskOutput(**res).model_dump()

        self.register(
            name="assign_task",
            description="Assign an operational Task to an authorized user/technician.",
            input_schema=AssignTaskInput,
            output_schema=AssignTaskOutput,
            handler=_exec_assign_task,
        )

        # 8. send_notification
        async def _exec_send_notif(params: SendNotificationInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.send_notification(
                recipient_user_id=params.recipient_user_id,
                title=params.title,
                message=params.message,
                channel=params.channel,
                priority=params.priority,
                correlation_headers=corrs,
            )
            return SendNotificationOutput(**res).model_dump()

        self.register(
            name="send_notification",
            description="Send in-app notification to campus stakeholders or assigned responders.",
            input_schema=SendNotificationInput,
            output_schema=SendNotificationOutput,
            handler=_exec_send_notif,
        )

        # 9. request_human_approval
        async def _exec_req_approval(params: RequestHumanApprovalInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.request_human_approval(
                incident_id=params.incident_id,
                proposed_action=params.proposed_action,
                reason=params.reason,
                required_role=params.required_role,
                estimated_cost=params.estimated_cost,
                correlation_headers=corrs,
            )
            return RequestHumanApprovalOutput(**res).model_dump()

        self.register(
            name="request_human_approval",
            description="Suspend automated action and request explicit authorization from campus supervisor.",
            input_schema=RequestHumanApprovalInput,
            output_schema=RequestHumanApprovalOutput,
            handler=_exec_req_approval,
        )

        # 10. escalate_incident
        async def _exec_escalate(params: EscalateIncidentInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.escalate_incident(
                incident_id=params.incident_id,
                escalation_reason=params.escalation_reason,
                correlation_headers=corrs,
            )
            return EscalateIncidentOutput(**res).model_dump()

        self.register(
            name="escalate_incident",
            description="Escalate high-severity incident to executive campus response team.",
            input_schema=EscalateIncidentInput,
            output_schema=EscalateIncidentOutput,
            handler=_exec_escalate,
        )

        # 11. record_resolution
        async def _exec_record_res(params: RecordResolutionInput, corrs: Dict[str, str]) -> Dict[str, Any]:
            res = await self.client.record_resolution(
                incident_id=params.incident_id,
                resolution_summary=params.resolution_summary,
                technician_id=params.technician_id,
                correlation_headers=corrs,
            )
            return RecordResolutionOutput(**res).model_dump()

        self.register(
            name="record_resolution",
            description="Record verified resolution notes and mark incident status as RESOLVED in Django Core.",
            input_schema=RecordResolutionInput,
            output_schema=RecordResolutionOutput,
            handler=_exec_record_res,
        )

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tenant_id: Optional[str] = None,
        correlation_headers: Optional[Dict[str, str]] = None,
    ) -> ToolExecutionRecord:
        """Executes tool with Pydantic validation and telemetry tracking."""
        tool = self.get_tool(tool_name)
        tool_call_id = f"tool_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        corrs = dict(correlation_headers or {})
        if tenant_id and "X-Tenant-ID" not in corrs:
            corrs["X-Tenant-ID"] = tenant_id
        corrs["X-Tool-Call-ID"] = tool_call_id

        if not tool:
            return ToolExecutionRecord(
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                inputs=arguments,
                output={},
                status="FAILED",
                error=f"Tool '{tool_name}' is not registered in ToolRegistry",
                duration_ms=round((time.time() - start_time) * 1000, 2),
                executed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

        try:
            # Validate input against typed schema
            validated_input = tool.input_schema(**arguments)
            # Execute handler
            result = await tool.handler(validated_input, corrs)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            return ToolExecutionRecord(
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                inputs=arguments,
                output=result if isinstance(result, dict) else {"result": result},
                status="SUCCESS",
                duration_ms=duration_ms,
                executed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        except ValidationError as val_err:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Tool {tool_name} input validation failed: {val_err}")
            return ToolExecutionRecord(
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                inputs=arguments,
                output={},
                status="FAILED",
                error=f"Schema validation error: {str(val_err)}",
                duration_ms=duration_ms,
                executed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Tool {tool_name} execution failed: {exc}", exc_info=True)
            return ToolExecutionRecord(
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                inputs=arguments,
                output={},
                status="FAILED",
                error=str(exc),
                duration_ms=duration_ms,
                executed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )


# Default global singleton
_default_registry: Optional[ToolRegistry] = None


def get_tool_registry(core_client: Optional[DjangoCoreClient] = None) -> ToolRegistry:
    global _default_registry
    if core_client is not None:
        return ToolRegistry(core_client=core_client)
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry
