"""
LangGraph Stateful Orchestration Graph for Paraxis AI Incidents.
Coordinates the multi-stage operational workflow:
Observe -> Understand -> Contextualize -> Detect -> Plan -> Policy Gate -> (Act / Human Gate) -> Monitor/Resolve.
Adheres to ADR-004.
"""
import uuid
import logging
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.nodes import (
    observe_node,
    understand_node,
    contextualize_node,
    detect_node,
    plan_node,
    policy_gate_node,
    human_gate_node,
    act_node,
    monitor_resolve_node,
)

logger = logging.getLogger("paraxis.agent.graph")


def route_policy_decision(state: IncidentAgentState) -> str:
    """
    Evaluates policy gate output to branch the execution path.
    """
    if not state.policy:
        return "act"

    if state.policy.decision == "REQUIRE_HUMAN_APPROVAL":
        logger.info(f"Routing to human_gate: {state.policy.reason}")
        return "human_gate"
    elif state.policy.decision == "DENY":
        logger.warning(f"Routing to monitor_resolve (Policy Denied): {state.policy.reason}")
        return "monitor_resolve"
    else:
        return "act"


def create_incident_state_graph() -> StateGraph:
    """Creates the uncompiled LangGraph StateGraph instance."""
    builder = StateGraph(IncidentAgentState)

    # Register nodes
    builder.add_node("observe", observe_node)
    builder.add_node("understand", understand_node)
    builder.add_node("contextualize", contextualize_node)
    builder.add_node("detect", detect_node)
    builder.add_node("plan", plan_node)
    builder.add_node("policy_gate", policy_gate_node)
    builder.add_node("human_gate", human_gate_node)
    builder.add_node("act", act_node)
    builder.add_node("monitor_resolve", monitor_resolve_node)

    # Core sequential analysis pipeline
    builder.add_edge(START, "observe")
    builder.add_edge("observe", "understand")
    builder.add_edge("understand", "contextualize")
    builder.add_edge("contextualize", "detect")
    builder.add_edge("detect", "plan")
    builder.add_edge("plan", "policy_gate")

    # Conditional policy enforcement branch
    builder.add_conditional_edges(
        "policy_gate",
        route_policy_decision,
        {
            "act": "act",
            "human_gate": "human_gate",
            "monitor_resolve": "monitor_resolve",
        },
    )

    # Terminal edges
    builder.add_edge("human_gate", END)
    builder.add_edge("act", "monitor_resolve")
    builder.add_edge("monitor_resolve", END)

    return builder


# Global In-Memory Checkpointer for state persistence and interruption
_global_checkpointer = MemorySaver()
_compiled_graph = None


def get_compiled_incident_graph(checkpointer: Optional[Any] = None):
    """Returns compiled graph with state checkpointer."""
    global _compiled_graph
    cp = checkpointer or _global_checkpointer
    if _compiled_graph is None or checkpointer is not None:
        builder = create_incident_state_graph()
        _compiled_graph = builder.compile(checkpointer=cp)
    return _compiled_graph


async def orchestrate_incident(
    initial_state: IncidentAgentState,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Primary entrypoint to orchestrate an incident workflow.
    """
    graph = get_compiled_incident_graph()
    t_id = thread_id or initial_state.incident_id or f"th_{uuid.uuid4().hex[:10]}"
    config = {"configurable": {"thread_id": t_id}}

    logger.info(f"Starting orchestration thread {t_id} for incident {initial_state.incident_id}")
    result = await graph.ainvoke(initial_state, config=config)
    return result


async def resume_orchestration(
    thread_id: str,
    approval_status: str,
    approver_role: str = "CAMPUS_ADMIN",
    reason: str = "",
) -> Dict[str, Any]:
    """
    Resumes a suspended workflow when a human operator grants or rejects approval.
    """
    graph = get_compiled_incident_graph()
    config = {"configurable": {"thread_id": thread_id}}

    # Retrieve checkpointed state
    current_state_snapshot = graph.get_state(config)
    if not current_state_snapshot or not current_state_snapshot.values:
        raise ValueError(f"No active or suspended workflow found for thread ID '{thread_id}'")

    current_values = current_state_snapshot.values
    state_obj = IncidentAgentState(**current_values)

    if approval_status == "APPROVED":
        logger.info(f"Resuming thread {thread_id}: Approval GRANTED by {approver_role}")
        # Transition from suspended to executing authorized action
        # 1. Update approval status
        updated_state = state_obj.model_copy(
            update={
                "approval_status": "APPROVED",
                "execution_status": "PENDING",
                "step_history": state_obj.step_history + ["human_approved"],
            }
        )
        # Execute act -> monitor_resolve
        act_res = await act_node(updated_state)
        merged_vals = updated_state.model_copy(update=act_res)
        final_res = await monitor_resolve_node(merged_vals)
        final_state = merged_vals.model_copy(update=final_res)

        # Update checkpoint
        graph.update_state(config, final_state.model_dump())
        return final_state.model_dump()
    else:
        logger.info(f"Resuming thread {thread_id}: Approval REJECTED by {approver_role}")
        updated_state = state_obj.model_copy(
            update={
                "approval_status": "REJECTED",
                "execution_status": "FAILED",
                "summary": f"Proposed action was rejected by {approver_role}. Reason: {reason}",
                "step_history": state_obj.step_history + ["human_rejected"],
            }
        )
        graph.update_state(config, updated_state.model_dump())
        return updated_state.model_dump()
