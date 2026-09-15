"""
Act Node: Executes authorized operational actions in Django Core via typed tools.
"""
import uuid
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.nodes.act")


async def act_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Executes pre-approved or human-authorized actions against Django Core.
    """
    logger.info(f"[{state.agent_run_id}] Executing authorized action: {state.proposal.action_type if state.proposal else 'NONE'}")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)
    prop = state.proposal
    idempotency_key = f"idem_{state.incident_id}_{uuid.uuid4().hex[:8]}"

    if prop and prop.action_type == "CREATE_TASK":
        task_title = f"{state.entities.category if state.entities else 'Incident'} Task: {state.raw_user_report[:50]}"
        task_record = await registry.execute(
            tool_name="create_incident_task",
            arguments={
                "incident_id": state.incident_id,
                "title": task_title,
                "instructions": state.raw_user_report,
                "priority": prop.priority,
                "department_id": prop.department_id,
                "idempotency_key": idempotency_key,
            },
            tenant_id=state.campus_id,
            correlation_headers=state.correlation_headers,
        )
        tools_executed.append(task_record)

        # Notify department supervisor
        notif_record = await registry.execute(
            tool_name="send_notification",
            arguments={
                "recipient_user_id": "usr_supervisor_01",
                "title": f"New Task Dispatched ({prop.priority})",
                "message": f"Task created for incident {state.incident_id} at {state.campus_context.get('room_number', 'campus')}",
                "channel": "IN_APP",
                "priority": "HIGH" if prop.priority in ["HIGH", "CRITICAL"] else "NORMAL",
            },
            tenant_id=state.campus_id,
            correlation_headers=state.correlation_headers,
        )
        tools_executed.append(notif_record)

    elif prop and prop.action_type == "LINK_DUPLICATE":
        # Record duplicate linking note
        dup_record = await registry.execute(
            tool_name="record_resolution",
            arguments={
                "incident_id": state.incident_id,
                "resolution_summary": f"Incident linked as duplicate of primary incident {state.duplicate.master_incident_id}",
            },
            tenant_id=state.campus_id,
            correlation_headers=state.correlation_headers,
        )
        tools_executed.append(dup_record)

    steps = list(state.step_history)
    if "act" not in steps:
        steps.append("act")

    return {
        "current_node": "act",
        "executed_tools": tools_executed,
        "step_history": steps,
    }
