"""
Detect Node: Evaluates incident similarity and detects duplicates/clusters.
Integrates pgvector semantic operational memory retrieval with location/asset context.
Adheres to Phase 6 Architecture Plan v2 and AGENTS.md guidelines.
"""
import logging
from typing import Dict, Any, List
from backend.intelligence.agent.state import IncidentAgentState, DuplicateAnalysis
from backend.intelligence.agent.tools.registry import get_tool_registry
from backend.intelligence.providers.factory import get_model_client

logger = logging.getLogger("paraxis.nodes.detect")

DUPLICATE_SIMILARITY_THRESHOLD = 0.85
RELATED_SIMILARITY_THRESHOLD = 0.70


async def detect_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Evaluates incident similarity against both active campus tickets and historical pgvector memory.
    Distinguishes between DUPLICATE (active identical problem in same space) and RELATED (historical precedent).
    """
    logger.info(f"[{state.agent_run_id}] Detecting duplicates and related operational incidents")

    registry = get_tool_registry()
    tools_executed = list(state.executed_tools)

    b_id = state.entities.building_id if state.entities else None
    r_id = state.entities.room_id if state.entities else None
    a_id = state.entities.asset_id if state.entities else None

    # 1. Semantic query embedding formulation (canonical 768 dimensions)
    model_client = get_model_client()
    query_embeddings = await model_client.embed([state.raw_user_report])
    query_vec = query_embeddings[0]

    # 2. Semantic Memory Retrieval via pgvector
    mem_record = await registry.execute(
        tool_name="search_operational_memory",
        arguments={
            "query_embedding": query_vec,
            "campus_id": state.campus_id,
            "source_type": "INCIDENT",
            "building_id": b_id,
            "room_id": r_id,
            "asset_id": a_id,
            "limit": 5,
        },
        tenant_id=state.campus_id,
        correlation_headers=state.correlation_headers,
    )
    tools_executed.append(mem_record)

    # 3. Active Related Incidents query (for real-time concurrent ticket correlation)
    rel_record = await registry.execute(
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
    tools_executed.append(rel_record)

    duplicate = DuplicateAnalysis(
        is_duplicate=False,
        similarity_score=0.0,
        relationship_type="NONE",
        rationale="No correlated operational incidents detected.",
    )

    # Examine active incident matches first
    active_matches = []
    if rel_record.status == "SUCCESS" and rel_record.output:
        active_matches = rel_record.output.get("matches", [])

    for m in active_matches:
        if m.get("incident_id") == state.incident_id:
            continue
        score = float(m.get("similarity_score", 0.0))
        status = m.get("status", "").upper()

        # Strict duplicate criterion: high semantic similarity + currently active/open lifecycle state
        if score >= DUPLICATE_SIMILARITY_THRESHOLD and status not in ["RESOLVED", "VERIFIED", "CLOSED"]:
            duplicate = DuplicateAnalysis(
                is_duplicate=True,
                master_incident_id=m.get("incident_id"),
                similarity_score=score,
                matched_incident_title=m.get("title"),
                relationship_type="DUPLICATE",
                rationale=f"High similarity ({score:.2f}) with active open ticket {m.get('incident_id')} in same location context.",
            )
            logger.info(
                f"[{state.agent_run_id}] Detected DUPLICATE ticket {m.get('incident_id')} (score={score:.2f})"
            )
            break
        elif score >= RELATED_SIMILARITY_THRESHOLD:
            duplicate = DuplicateAnalysis(
                is_duplicate=False,
                master_incident_id=m.get("incident_id"),
                similarity_score=score,
                matched_incident_title=m.get("title"),
                relationship_type="RELATED",
                rationale=f"Related concurrent ticket {m.get('incident_id')} (score={score:.2f}), but distinct operational work.",
            )

    # If no active duplicate found, check semantic memory matches
    if not duplicate.is_duplicate and mem_record.status == "SUCCESS" and mem_record.output:
        mem_results = mem_record.output.get("results", [])
        for r in mem_results:
            if r.get("source_id") == state.incident_id:
                continue
            sim = float(r.get("similarity_score", 0.0))
            if sim >= RELATED_SIMILARITY_THRESHOLD and not duplicate.master_incident_id:
                duplicate = DuplicateAnalysis(
                    is_duplicate=False,
                    master_incident_id=r.get("source_id"),
                    similarity_score=sim,
                    matched_incident_title=r.get("title"),
                    relationship_type="RELATED",
                    rationale=f"Identified historical operational precedent from memory (similarity={sim:.2f}).",
                )

    steps = list(state.step_history)
    if "detect" not in steps:
        steps.append("detect")

    return {
        "current_node": "detect",
        "duplicate": duplicate,
        "executed_tools": tools_executed,
        "step_history": steps,
    }
