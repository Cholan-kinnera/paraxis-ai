"""
Incident Orchestration API Endpoints for Paraxis AI.
Provides orchestrate and resume endpoints driving LangGraph workflows.
Adheres to ADR-004, ADR-007, and AGENTS.md guidelines.
"""
import uuid
import logging
from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, Request, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.intelligence.agent.state import (
    IncidentAgentState,
    EntityResolution,
    DuplicateAnalysis,
    ActionProposal,
    PolicyEvaluation,
    ToolExecutionRecord,
)
from backend.intelligence.agent.graph import orchestrate_incident, resume_orchestration

logger = logging.getLogger("paraxis.api.orchestrate")

router = APIRouter()


class OrchestrateIncidentRequest(BaseModel):
    incident_id: str
    raw_user_report: str
    organization_id: Optional[str] = None
    campus_id: Optional[str] = None
    reporter_id: Optional[str] = ""


class ResumeOrchestrationRequest(BaseModel):
    thread_id: str
    approval_status: Literal["APPROVED", "REJECTED"]
    approver_role: str = "CAMPUS_ADMIN"
    reason: Optional[str] = ""


class IncidentOrchestrationResponseData(BaseModel):
    incident_id: str
    agent_run_id: str
    execution_status: str
    current_node: str
    entities: Optional[EntityResolution] = None
    duplicate: Optional[DuplicateAnalysis] = None
    policy: Optional[PolicyEvaluation] = None
    proposal: Optional[ActionProposal] = None
    approval_id: Optional[str] = None
    approval_status: Optional[str] = None
    summary: str
    step_history: List[str]
    executed_tools: List[ToolExecutionRecord] = Field(default_factory=list)


@router.post(
    "/orchestrate/incident",
    status_code=status.HTTP_200_OK,
    summary="Orchestrate incident operational workflow through LangGraph",
)
async def orchestrate_incident_endpoint(
    payload: OrchestrateIncidentRequest,
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID"),
):
    """
    Ingests incident report, executes multi-node operational reasoning,
    evaluates policy constraints, and coordinates task dispatch or approval request.
    """
    req_id = x_request_id or f"req_{uuid.uuid4().hex[:12]}"
    trace_id = x_trace_id or f"trace_{uuid.uuid4().hex[:16]}"
    # Multi-tenancy: derive tenant from header per ADR-001 / AGENTS.md Section 2.2
    tenant_id = x_tenant_id or payload.campus_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required. Provide 'X-Tenant-ID' header or campus_id.",
        )

    correlation_headers = {
        "X-Request-ID": req_id,
        "X-Trace-ID": trace_id,
        "X-Tenant-ID": tenant_id,
    }

    initial_state = IncidentAgentState(
        incident_id=payload.incident_id,
        organization_id=payload.organization_id or f"org_{tenant_id}",
        campus_id=tenant_id,
        reporter_id=payload.reporter_id or "",
        raw_user_report=payload.raw_user_report,
        correlation_headers=correlation_headers,
    )

    try:
        result_dict = await orchestrate_incident(initial_state, thread_id=payload.incident_id)

        response_data = IncidentOrchestrationResponseData(
            incident_id=result_dict.get("incident_id", payload.incident_id),
            agent_run_id=result_dict.get("agent_run_id", ""),
            execution_status=result_dict.get("execution_status", "SUCCESS"),
            current_node=result_dict.get("current_node", ""),
            entities=result_dict.get("entities"),
            duplicate=result_dict.get("duplicate"),
            policy=result_dict.get("policy"),
            proposal=result_dict.get("proposal"),
            approval_id=result_dict.get("approval_id"),
            approval_status=result_dict.get("approval_status"),
            summary=result_dict.get("summary", ""),
            step_history=result_dict.get("step_history", []),
            executed_tools=result_dict.get("executed_tools", []),
        )

        return {
            "status": "success",
            "data": response_data.model_dump(),
            "meta": {
                "request_id": req_id,
                "trace_id": trace_id,
                "tenant_id": tenant_id,
            },
        }
    except Exception as exc:
        logger.error(f"Orchestration failure for incident {payload.incident_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution error: {str(exc)}",
        )


@router.post(
    "/orchestrate/resume",
    status_code=status.HTTP_200_OK,
    summary="Resume suspended workflow following human approval or rejection",
)
async def resume_orchestration_endpoint(
    payload: ResumeOrchestrationRequest,
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID"),
):
    """
    Resumes an interrupted or suspended incident workflow from checkpoint.
    """
    req_id = x_request_id or f"req_{uuid.uuid4().hex[:12]}"
    trace_id = x_trace_id or f"trace_{uuid.uuid4().hex[:16]}"

    try:
        resumed_dict = await resume_orchestration(
            thread_id=payload.thread_id,
            approval_status=payload.approval_status,
            approver_role=payload.approver_role,
            reason=payload.reason or "",
        )

        response_data = IncidentOrchestrationResponseData(
            incident_id=resumed_dict.get("incident_id", payload.thread_id),
            agent_run_id=resumed_dict.get("agent_run_id", ""),
            execution_status=resumed_dict.get("execution_status", "SUCCESS"),
            current_node=resumed_dict.get("current_node", ""),
            entities=resumed_dict.get("entities"),
            duplicate=resumed_dict.get("duplicate"),
            policy=resumed_dict.get("policy"),
            proposal=resumed_dict.get("proposal"),
            approval_id=resumed_dict.get("approval_id"),
            approval_status=resumed_dict.get("approval_status"),
            summary=resumed_dict.get("summary", ""),
            step_history=resumed_dict.get("step_history", []),
            executed_tools=resumed_dict.get("executed_tools", []),
        )

        return {
            "status": "success",
            "data": response_data.model_dump(),
            "meta": {
                "request_id": req_id,
                "trace_id": trace_id,
            },
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.error(f"Error resuming thread {payload.thread_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume orchestration: {str(exc)}",
        )
