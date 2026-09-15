"""
Formal State Schema for Paraxis AI LangGraph Orchestration.
Adheres to ADR-004 and docs/agents/agent-state-model.md.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class EntityResolution(BaseModel):
    category: str = "OTHER"
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    room_id: Optional[str] = None
    room_number: Optional[str] = None
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    confidence: float = 0.0


class DuplicateAnalysis(BaseModel):
    is_duplicate: bool = False
    master_incident_id: Optional[str] = None
    similarity_score: float = 0.0
    matched_incident_title: Optional[str] = None


class ActionProposal(BaseModel):
    action_type: Literal["CREATE_TASK", "ASSIGN_TASK", "LINK_DUPLICATE", "REQUEST_APPROVAL", "ESCALATE"] = "CREATE_TASK"
    department_id: Optional[str] = None
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    assigned_user_id: Optional[str] = None
    estimated_cost: float = 0.0
    action_justification: str = ""
    target_campus_id: Optional[str] = None


class PolicyEvaluation(BaseModel):
    decision: Literal["ALLOW", "DENY", "REQUIRE_HUMAN_APPROVAL"] = "ALLOW"
    rule_id: Optional[str] = None
    reason: str = ""
    required_approver_role: Optional[str] = None


class ToolExecutionRecord(BaseModel):
    tool_name: str
    tool_call_id: str = ""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    status: str = "SUCCESS"
    executed_at: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None


class IncidentAgentState(BaseModel):
    """
    Immutable state passed across LangGraph nodes.
    Checkpointed at node boundaries.
    """
    # Context & Identifiers
    incident_id: str
    organization_id: str
    campus_id: str
    reporter_id: str = ""
    raw_user_report: str

    # Progress Tracking
    current_node: str = "observe"
    step_history: List[str] = Field(default_factory=list)

    # Analysis & Graph Matching
    entities: Optional[EntityResolution] = None
    duplicate: Optional[DuplicateAnalysis] = None
    campus_context: Dict[str, Any] = Field(default_factory=dict)

    # Action & Policy Evaluation
    proposal: Optional[ActionProposal] = None
    policy: Optional[PolicyEvaluation] = None
    approval_id: Optional[str] = None
    approval_status: Optional[Literal["PENDING", "APPROVED", "REJECTED"]] = None

    # Execution, Telemetry & Diagnostics
    executed_tools: List[ToolExecutionRecord] = Field(default_factory=list)
    execution_status: Literal["PENDING", "SUCCESS", "FAILED", "SUSPENDED"] = "PENDING"
    error_messages: List[str] = Field(default_factory=list)
    summary: str = ""
    agent_run_id: str = ""
    correlation_headers: Dict[str, str] = Field(default_factory=dict)
