"""
Contextualize Node: Resolves physical location and retrieves operational insights.
Enriches state with building, room, connected IoT assets, and active recurring problem insights.
Adheres to ADR-003, Phase 6 Architecture Plan v2, and AGENTS.md guidelines.
"""
import logging
from typing import Dict, Any, List
from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.tools.registry import get_tool_registry

logger = logging.getLogger("paraxis.nodes.contextualize")


async def contextualize_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Enriches state with building, room, and asset context from the campus graph,
    and attaches relevant active institutional knowledge insights.
    """
    logger.info(f"[{state.agent_run_id}] Contextualizing location and operational insights")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)
    campus_context = dict(state.campus_context)
    entities = state.entities.model_copy() if state.entities else None

    b_name = entities.building_name if entities and entities.building_name else "Main Campus"
    r_num = entities.room_number if entities and entities.room_number else "101"

    # 1. Resolve Location Context from Django Core Campus Graph
    loc_record = await registry.execute(
        tool_name="get_location_context",
        arguments={
            "building_name": b_name,
            "room_number": r_num,
            "campus_id": state.campus_id,
        },
        tenant_id=state.campus_id,
        correlation_headers=state.correlation_headers,
    )
    tools_executed.append(loc_record)

    if loc_record.status == "SUCCESS" and loc_record.output:
        loc_data = loc_record.output
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

    # 2. Retrieve Relevant Active Operational Insights from Django Core
    insights_list: List[Dict[str, Any]] = []
    asset_id = entities.asset_id if entities else None
    room_id = entities.room_id if entities else None

    insight_record = await registry.execute(
        tool_name="get_operational_insights",
        arguments={
            "campus_id": state.campus_id,
            "target_asset_id": asset_id,
            "target_room_id": room_id,
            "status": "ACTIVE",
        },
        tenant_id=state.campus_id,
        correlation_headers=state.correlation_headers,
    )
    tools_executed.append(insight_record)

    if insight_record.status == "SUCCESS" and insight_record.output:
        insights_list = insight_record.output.get("insights", [])
        if insights_list:
            logger.info(
                f"[{state.agent_run_id}] Attached {len(insights_list)} active operational insights to context"
            )

    steps = list(state.step_history)
    if "contextualize" not in steps:
        steps.append("contextualize")

    return {
        "current_node": "contextualize",
        "campus_context": campus_context,
        "entities": entities,
        "operational_insights": insights_list,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
