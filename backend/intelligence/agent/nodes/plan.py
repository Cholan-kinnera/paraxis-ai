"""
Plan Node: Synthesizes contextual intelligence and formulates an actionable operational proposal.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState, ActionProposal
from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.nodes.plan")


async def plan_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Formulates operational action plan based on location, severity, and duplicates.
    """
    logger.info(f"[{state.agent_run_id}] Formulating action plan")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)

    # If already identified as duplicate, propose linking rather than creating a redundant task
    if state.duplicate and state.duplicate.is_duplicate:
        proposal = ActionProposal(
            action_type="LINK_DUPLICATE",
            priority="LOW",
            action_justification=f"Correlated as duplicate of active incident {state.duplicate.master_incident_id}",
            target_campus_id=state.campus_id,
        )
    else:
        # Evaluate priority via deterministic tool
        cat = state.entities.category if state.entities else "OTHER"
        report_lower = state.raw_user_report.lower()
        is_urgent = any(w in report_lower for w in ["urgent", "emergency", "fire", "danger", "immediately", "hazard"])
        affected = 60 if any(w in report_lower for w in ["auditorium", "lecture hall", "entire floor", "campus wide"]) else 5

        prio_record = await registry.execute(
            tool_name="calculate_priority",
            arguments={
                "category": cat,
                "room_type": state.campus_context.get("room_number", ""),
                "student_count_affected": affected,
                "urgency_flag": is_urgent,
            },
            tenant_id=state.campus_id,
            correlation_headers=state.correlation_headers,
        )
        tools_executed.append(prio_record)

        priority = "MEDIUM"
        if prio_record.status == "SUCCESS" and prio_record.output:
            priority = prio_record.output.get("priority", "MEDIUM")

        # Map department
        dept_map = {
            "FACILITIES": "dept_facilities_01",
            "IT": "dept_it_network_01",
            "SAFETY": "dept_campus_security_01",
            "ACADEMIC": "dept_academic_affairs_01",
        }
        dept_id = dept_map.get(cat.upper(), "dept_general_ops_01")

        # Estimate cost
        estimated_cost = 0.0
        if "hvac" in report_lower or "chiller" in report_lower:
            estimated_cost = 750.0  # triggers human approval (>$500)
        elif "pipe burst" in report_lower:
            estimated_cost = 600.0
        elif "projector" in report_lower or "cable" in report_lower:
            estimated_cost = 150.0

        proposal = ActionProposal(
            action_type="CREATE_TASK",
            department_id=dept_id,
            priority=priority,
            estimated_cost=estimated_cost,
            action_justification=f"Automated resolution plan for {cat} incident with priority {priority}",
            target_campus_id=state.campus_id,
        )

    steps = list(state.step_history)
    if "plan" not in steps:
        steps.append("plan")

    return {
        "current_node": "plan",
        "proposal": proposal,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
