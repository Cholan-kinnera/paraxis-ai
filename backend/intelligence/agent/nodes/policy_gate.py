"""
Policy Gate Node: Enforces deterministic safety, financial, and multi-tenant security rules.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.policy import PolicyEngine

logger = logging.getLogger("paraxis.nodes.policy_gate")


async def policy_gate_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Evaluates proposed action through the deterministic policy engine.
    """
    logger.info(f"[{state.agent_run_id}] Evaluating policy for proposal: {state.proposal.action_type if state.proposal else 'NONE'}")

    context = {
        "incident_id": state.incident_id,
        "campus_id": state.campus_id,
        "organization_id": state.organization_id,
        "category": state.entities.category if state.entities else "OTHER",
        "raw_text": state.raw_user_report,
    }

    evaluation = PolicyEngine.evaluate(state.proposal, context)

    logger.info(
        f"[{state.agent_run_id}] Policy outcome: {evaluation.decision} "
        f"(Rule: {evaluation.rule_id}, Reason: {evaluation.reason})"
    )

    steps = list(state.step_history)
    if "policy_gate" not in steps:
        steps.append("policy_gate")

    return {
        "current_node": "policy_gate",
        "policy": evaluation,
        "step_history": steps,
    }
