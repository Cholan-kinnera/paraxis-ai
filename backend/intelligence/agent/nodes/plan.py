"""
Plan Node: Synthesizes contextual intelligence and formulates an actionable operational proposal.
Retrieves historical resolution precedents from pgvector memory and grounds proposals in verified FACT.
Adheres to Phase 6 Architecture Plan v2 and AGENTS.md guidelines.
"""
import logging
from typing import Dict, Any, List
from backend.intelligence.agent.state import IncidentAgentState, ActionProposal
from backend.intelligence.agent.tools.registry import get_tool_registry
from backend.intelligence.providers.factory import get_model_client

logger = logging.getLogger("paraxis.nodes.plan")


async def plan_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Formulates operational action plan grounded in empirical historical resolution precedents.
    Exposes prior resolutions explicitly as FACT and preserves policy governance boundaries.
    """
    logger.info(f"[{state.agent_run_id}] Formulating operational action plan grounded in memory")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)
    precedents: List[Dict[str, Any]] = []

    # 1. If duplicate detected, propose linking rather than redundant task creation
    if state.duplicate and state.duplicate.is_duplicate:
        proposal = ActionProposal(
            action_type="LINK_DUPLICATE",
            priority="LOW",
            action_justification=(
                f"DUPLICATE DETECTED: Correlated as duplicate of active ticket "
                f"{state.duplicate.master_incident_id} (Similarity: {state.duplicate.similarity_score:.2f}). "
                f"Rationale: {state.duplicate.rationale}"
            ),
            target_campus_id=state.campus_id,
        )
    else:
        # 2. Retrieve Historical Resolution Precedents from pgvector memory
        model_client = get_model_client()
        query_vec = (await model_client.embed([state.raw_user_report]))[0]

        cat = state.entities.category if state.entities else "OTHER"
        b_id = state.entities.building_id if state.entities else None
        r_id = state.entities.room_id if state.entities else None

        mem_record = await registry.execute(
            tool_name="search_operational_memory",
            arguments={
                "query_embedding": query_vec,
                "campus_id": state.campus_id,
                "source_type": "INCIDENT",
                "category": cat if cat != "OTHER" else None,
                "building_id": b_id,
                "limit": 3,
            },
            tenant_id=state.campus_id,
            correlation_headers=state.correlation_headers,
        )
        tools_executed.append(mem_record)

        if mem_record.status == "SUCCESS" and mem_record.output:
            precedents = mem_record.output.get("results", [])

        # 3. Evaluate deterministic priority via tool
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

        # Map functional department
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

        # Construct justification with verified precedent facts
        justification_parts = [f"Automated resolution plan for {cat} incident with priority {priority}."]

        # Grounding: Reference active recurring problem insights if present
        if state.operational_insights:
            first_insight = state.operational_insights[0]
            justification_parts.append(
                f"[INSTITUTIONAL KNOWLEDGE]: Active recurring anomaly recognized ({first_insight.get('insight_type')}). "
                f"Recommended procedure: {first_insight.get('recommendation')[:120]}..."
            )

        # Grounding: Reference historical resolution precedents explicitly as FACT
        if precedents:
            best_precedent = precedents[0]
            justification_parts.append(
                f"[FACT PRECEDENT]: Historical incident {best_precedent.get('source_id')} "
                f"(Similarity: {best_precedent.get('similarity_score', 0):.2f}) - {best_precedent.get('title')}."
            )

        proposal = ActionProposal(
            action_type="CREATE_TASK",
            department_id=dept_id,
            priority=priority,
            estimated_cost=estimated_cost,
            action_justification=" ".join(justification_parts),
            target_campus_id=state.campus_id,
        )

    steps = list(state.step_history)
    if "plan" not in steps:
        steps.append("plan")

    return {
        "current_node": "plan",
        "proposal": proposal,
        "memory_precedents": precedents,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
