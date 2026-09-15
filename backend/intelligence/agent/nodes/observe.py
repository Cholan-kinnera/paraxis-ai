"""
Observe Node: Initial ingestion, sanitization, and correlation context setup.
"""
import uuid
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState

logger = logging.getLogger("paraxis.nodes.observe")


async def observe_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Ingests and normalizes the initial incident observation.
    Establishes tracing correlation headers.
    """
    agent_run_id = state.agent_run_id or f"run_{uuid.uuid4().hex[:12]}"
    clean_report = state.raw_user_report.strip()

    corrs = dict(state.correlation_headers)
    corrs.setdefault("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    corrs.setdefault("X-Trace-ID", f"trace_{uuid.uuid4().hex[:16]}")
    corrs.setdefault("X-Tenant-ID", state.campus_id)
    corrs["X-Agent-Run-ID"] = agent_run_id

    logger.info(
        f"[{agent_run_id}] Observational ingestion started for incident {state.incident_id} "
        f"on campus {state.campus_id}"
    )

    steps = list(state.step_history)
    if "observe" not in steps:
        steps.append("observe")

    return {
        "current_node": "observe",
        "agent_run_id": agent_run_id,
        "raw_user_report": clean_report,
        "correlation_headers": corrs,
        "step_history": steps,
        "execution_status": "PENDING",
    }
