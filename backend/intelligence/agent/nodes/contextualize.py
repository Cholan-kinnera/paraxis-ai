"""
Contextualize Node: Resolves physical location and connected IoT assets against Django Core Campus Graph.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.nodes.contextualize")


async def contextualize_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Enriches state with building, room, and asset context from the campus graph.
    """
    logger.info(f"[{state.agent_run_id}] Contextualizing location from campus graph")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)
    campus_context = dict(state.campus_context)
    entities = state.entities.model_copy() if state.entities else None

    b_name = entities.building_name if entities and entities.building_name else "Main Campus"
    r_num = entities.room_number if entities and entities.room_number else "101"

    # Execute typed tool
    record = await registry.execute(
        tool_name="get_location_context",
        arguments={
            "building_name": b_name,
            "room_number": r_num,
            "campus_id": state.campus_id,
        },
        tenant_id=state.campus_id,
        correlation_headers=state.correlation_headers,
    )
    tools_executed.append(record)

    if record.status == "SUCCESS" and record.output:
        loc_data = record.output
        campus_context.update(loc_data)
        if entities:
            if loc_data.get("building_id"):
                entities.building_id = loc_data["building_id"]
            if loc_data.get("room_id"):
                entities.room_id = loc_data["room_id"]
            assets = loc_data.get("assets", [])
            if assets and isinstance(assets, list) and len(assets) > 0:
                entities.asset_id = assets[0].get("asset_id")
                entities.asset_name = assets[0].get("name")

    steps = list(state.step_history)
    if "contextualize" not in steps:
        steps.append("contextualize")

    return {
        "current_node": "contextualize",
        "campus_context": campus_context,
        "entities": entities,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
