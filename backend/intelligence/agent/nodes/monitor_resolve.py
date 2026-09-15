"""
Monitor & Resolve Node: Final state synthesis, structured operational summary, and audit logging.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState

logger = logging.getLogger("paraxis.nodes.monitor_resolve")


async def monitor_resolve_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Synthesizes execution telemetry and produces an auditable operational outcome summary.
    """
    logger.info(f"[{state.agent_run_id}] Finalizing operational outcome")

    steps = list(state.step_history)
    if "monitor_resolve" not in steps:
        steps.append("monitor_resolve")

    errors = list(state.error_messages)

    # Check if policy denied
    if state.policy and state.policy.decision == "DENY":
        status = "FAILED"
        err_msg = f"Proposal rejected by Policy Engine ({state.policy.rule_id}): {state.policy.reason}"
        errors.append(err_msg)
        summary = err_msg
    else:
        # Check tool execution statuses
        failed_tools = [t for t in state.executed_tools if t.status == "FAILED"]
        if failed_tools:
            status = "FAILED"
            for ft in failed_tools:
                errors.append(f"Tool {ft.tool_name} failed: {ft.error}")
            summary = f"Workflow completed with errors in {len(failed_tools)} tool call(s)."
        else:
            status = "SUCCESS"
            cat = state.entities.category if state.entities else "Operational"
            bld = state.campus_context.get("building_name", "Campus")
            room = state.campus_context.get("room_number", "")
            action_desc = state.proposal.action_type if state.proposal else "Action"
            summary = (
                f"Successfully coordinated {cat} response at {bld} {room}. "
                f"Action '{action_desc}' executed under priority {state.proposal.priority if state.proposal else 'NORMAL'}. "
                f"Tools executed: {len(state.executed_tools)}."
            )

    return {
        "current_node": "monitor_resolve",
        "execution_status": status,
        "error_messages": errors,
        "summary": summary,
        "step_history": steps,
    }
