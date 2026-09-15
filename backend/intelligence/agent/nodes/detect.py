"""
Detect Node: Evaluates incident similarity and detects duplicates/clusters.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState, DuplicateAnalysis
from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.nodes.detect")


async def detect_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Searches recent incidents to identify duplicates or systemic recurring failures.
    """
    logger.info(f"[{state.agent_run_id}] Detecting duplicates and related incidents")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)

    b_id = state.entities.building_id if state.entities else None
    r_id = state.entities.room_id if state.entities else None

    record = await registry.execute(
        tool_name="search_related_incidents",
        arguments={
            "query_text": state.raw_user_report,
            "campus_id": state.campus_id,
            "building_id": b_id,
            "room_id": r_id,
            "limit": 5,
        },
        tenant_id=state.campus_id,
        correlation_headers=state.correlation_headers,
    )
    tools_executed.append(record)

    duplicate = DuplicateAnalysis(is_duplicate=False, similarity_score=0.0)

    if record.status == "SUCCESS" and record.output:
        matches = record.output.get("matches", [])
        for m in matches:
            # Check if there is another open incident with high similarity
            if m.get("incident_id") != state.incident_id and m.get("similarity_score", 0.0) >= 0.80:
                duplicate = DuplicateAnalysis(
                    is_duplicate=True,
                    master_incident_id=m.get("incident_id"),
                    similarity_score=m.get("similarity_score"),
                    matched_incident_title=m.get("title"),
                )
                logger.info(
                    f"[{state.agent_run_id}] Detected duplicate incident {m.get('incident_id')} "
                    f"with score {m.get('similarity_score')}"
                )
                break

    steps = list(state.step_history)
    if "detect" not in steps:
        steps.append("detect")

    return {
        "current_node": "detect",
        "duplicate": duplicate,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
