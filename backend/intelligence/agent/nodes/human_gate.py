"""
Human Gate Node: Manages human approval boundary for sensitive, costly, or safety-critical actions.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.nodes.human_gate")


async def human_gate_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Submits a pending approval ticket and suspends autonomous workflow.
    """
    logger.info(f"[{state.agent_run_id}] Suspending workflow for human approval")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)

    prop = state.proposal
    pol = state.policy

    record = await registry.execute(
        tool_name="request_human_approval",
        arguments={
            "incident_id": state.incident_id,
            "proposed_action": prop.action_type if prop else "CREATE_TASK",
            "reason": pol.reason if pol else "Policy requires supervisor approval",
            "required_role": pol.required_approver_role if pol and pol.required_approver_role else "CAMPUS_ADMIN",
            "estimated_cost": prop.estimated_cost if prop else 0.0,
        },
        tenant_id=state.campus_id,
        correlation_headers=state.correlation_headers,
    )
    tools_executed.append(record)

    approval_id = record.output.get("approval_id") if record.status == "SUCCESS" and record.output else "appr_pending"

    steps = list(state.step_history)
    if "human_gate" not in steps:
        steps.append("human_gate")

    summary_msg = (
        f"Workflow suspended: human authorization required by {pol.required_approver_role if pol else 'CAMPUS_ADMIN'} "
        f"for {prop.action_type if prop else 'ACTION'} (Reason: {pol.reason if pol else 'Policy'}). "
        f"Approval Request ID: {approval_id}"
    )

    return {
        "current_node": "human_gate",
        "approval_id": approval_id,
        "approval_status": "PENDING",
        "execution_status": "SUSPENDED",
        "summary": summary_msg,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
