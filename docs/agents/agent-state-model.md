# Agent State Model (`IncidentAgentState`) — Paraxis AI

> **Purpose**: Formal definition of the state schema passed between LangGraph nodes, checkpointing strategy, and state reduction rules.

---

## 1. Schema Definition

```python
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class EntityResolution(BaseModel):
    category: str
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
    action_type: Literal["CREATE_TASK", "ASSIGN_TASK", "LINK_DUPLICATE", "REQUEST_APPROVAL", "ESCALATE"]
    department_id: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assigned_user_id: Optional[str] = None
    estimated_cost: float = 0.0
    action_justification: str

class PolicyEvaluation(BaseModel):
    decision: Literal["ALLOW", "DENY", "REQUIRE_HUMAN_APPROVAL"]
    rule_id: Optional[str] = None
    reason: str
    required_approver_role: Optional[str] = None

class IncidentAgentState(BaseModel):
    """
    Immutable state passed across LangGraph nodes.
    Checkpointed in Redis / PostgreSQL at each node boundary.
    """
    # Context & Identifiers
    incident_id: str
    organization_id: str
    campus_id: str
    reporter_id: str
    raw_user_report: str
    
    # Progress Tracking
    current_node: str = "observe"
    step_history: List[str] = []
    
    # Analysis & Graph Matching
    entities: Optional[EntityResolution] = None
    duplicate: Optional[DuplicateAnalysis] = None
    campus_context: Dict[str, Any] = {}
    
    # Action & Policy
    proposal: Optional[ActionProposal] = None
    policy: Optional[PolicyEvaluation] = None
    approval_id: Optional[str] = None
    
    # Execution & Telemetry
    executed_tools: List[Dict[str, Any]] = []
    execution_status: Literal["PENDING", "SUCCESS", "FAILED", "SUSPENDED"] = "PENDING"
    error_messages: List[str] = []
```

---

## 2. Checkpointing & State Persistence

LangGraph utilizes a Redis-backed checkpoint saver (`RedisSaver`) in development and PostgreSQL-backed saver (`PostgresSaver`) in enterprise deployments. 
- When an action triggers `REQUIRE_HUMAN_APPROVAL`, the graph thread suspends with state preserved.
- When human approval is registered in Django Core, a webhook resumes the thread with `approval_status: APPROVED`.
