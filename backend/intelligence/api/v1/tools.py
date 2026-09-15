"""
Tool Management and Direct Execution Endpoints.
Allows querying registered tool definitions and performing policy-gated direct execution.
"""
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.api.tools")

router = APIRouter()


class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    tenant_id: Optional[str] = None


@router.get(
    "/tools",
    status_code=status.HTTP_200_OK,
    summary="List all registered typed operational tools",
)
async def list_tools_endpoint():
    """
    Returns list of all available operational tools and their schemas.
    """
    registry = get_tool_registry()
    tools = registry.list_tools()
    return {
        "status": "success",
        "data": {
            "count": len(tools),
            "tools": tools,
        },
    }


@router.post(
    "/tools/execute",
    status_code=status.HTTP_200_OK,
    summary="Execute a registered tool directly with schema validation and tracing",
)
async def execute_tool_endpoint(
    payload: ToolExecuteRequest,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID"),
):
    """
    Executes a single tool action with Pydantic validation and telemetry tracking.
    """
    registry = get_tool_registry()
    tool = registry.get_tool(payload.tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{payload.tool_name}' is not registered in ToolRegistry",
        )

    tenant = x_tenant_id or payload.tenant_id
    correlation_headers = {
        "X-Request-ID": x_request_id or f"req_{uuid.uuid4().hex[:12]}",
        "X-Trace-ID": x_trace_id or f"trace_{uuid.uuid4().hex[:16]}",
        "X-Tenant-ID": tenant or "",
    }

    record = await registry.execute(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        tenant_id=tenant,
        correlation_headers=correlation_headers,
    )

    if record.status == "FAILED":
        return {
            "status": "error",
            "data": record.model_dump(),
            "message": record.error,
        }

    return {
        "status": "success",
        "data": record.model_dump(),
    }
