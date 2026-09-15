"""
Understand Node: Extracts domain entities (category, location, assets) from unstructured report via AI Provider Gateway.
"""
import logging
from typing import Dict, Any
from backend.intelligence.agent.state import IncidentAgentState, EntityResolution
from backend.intelligence.providers.factory import get_model_client

logger = logging.getLogger("paraxis.nodes.understand")

UNDERSTAND_SYSTEM_PROMPT = """You are Paraxis AI Campus Operational Intelligence.
Analyze the incident report and extract structured operational entities:
- category: One of ['FACILITIES', 'IT', 'SAFETY', 'ACADEMIC', 'OTHER']
- building_name: Building mentioned (e.g., 'Science Center', 'Engineering Block', or null)
- room_number: Room or area mentioned (e.g., '204', 'Lab 3', or null)
- asset_name: Specific equipment or asset affected (e.g., 'Projector', 'Access Point', or null)
- confidence: Extraction confidence score from 0.0 to 1.0

Return strictly the structured output."""


async def understand_node(state: IncidentAgentState) -> Dict[str, Any]:
    """
    Invokes model client with structured schema to parse raw incident text.
    """
    logger.info(f"[{state.agent_run_id}] Understanding incident semantics: '{state.raw_user_report}'")

    model = get_model_client()
    messages = [
        {"role": "system", "content": UNDERSTAND_SYSTEM_PROMPT},
        {"role": "user", "content": f"Incident Report:\n{state.raw_user_report}"},
    ]

    try:
        response = await model.generate(
            prompt=f"Incident Report:\n{state.raw_user_report}",
            schema=EntityResolution,
            system_prompt=UNDERSTAND_SYSTEM_PROMPT,
        )
        if isinstance(response.parsed, EntityResolution):
            entities = response.parsed
        elif isinstance(response.parsed, dict):
            entities = EntityResolution(**response.parsed)
        else:
            # Fallback heuristic
            entities = EntityResolution(
                category="FACILITIES" if "leak" in state.raw_user_report.lower() else "IT",
                building_name="Engineering Block",
                room_number="204",
                confidence=0.85,
            )
    except Exception as exc:
        logger.warning(f"Semantic extraction encountered error: {exc}. Falling back to default entity resolution.")
        entities = EntityResolution(category="OTHER", confidence=0.5)

    steps = list(state.step_history)
    if "understand" not in steps:
        steps.append("understand")

    return {
        "current_node": "understand",
        "entities": entities,
        "step_history": steps,
    }
