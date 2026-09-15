"""
Integration Tests for Phase 5: Paraxis AI Intelligence Layer.
Covers AI Provider Gateway, Policy Engine Invariants, Typed Tool Registry,
LangGraph Stateful Orchestration, and FastAPI Orchestration Endpoints.
Adheres to ADR-004, ADR-005, ADR-008, and AGENTS.md guidelines.
"""
import uuid
import pytest
import httpx
from fastapi.testclient import TestClient

from backend.intelligence.main import app
from backend.intelligence.providers.mock_adapter import MockModelAdapter
from backend.intelligence.providers.factory import get_model_client
from backend.intelligence.agent.state import (
    IncidentAgentState,
    EntityResolution,
    ActionProposal,
)
from backend.intelligence.agent.policy import PolicyEngine
from backend.intelligence.agent.tools.registry import ToolRegistry, get_tool_registry
from backend.intelligence.agent.graph import orchestrate_incident, resume_orchestration


# ---------------------------------------------------------------------------
# 1. AI Provider Gateway Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provider_gateway_mock_adapter_structured_generation():
    """Validates that model gateway generates structured Pydantic objects."""
    adapter = MockModelAdapter()
    resp = await adapter.generate(
        prompt="Water pipe broken in Room 204 Engineering Block",
        schema=EntityResolution,
    )
    assert resp.parsed is not None
    assert isinstance(resp.parsed, EntityResolution)
    assert resp.parsed.room_number == "204"
    assert resp.parsed.category == "PLUMBING"
    assert resp.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_provider_gateway_fallback_factory():
    """Validates fallback to MockModelAdapter when API keys are unconfigured."""
    client = get_model_client("mock")
    assert isinstance(client, MockModelAdapter)


@pytest.mark.asyncio
async def test_provider_gateway_streaming_and_embeddings():
    """Validates token streaming iterator and vector embeddings generation."""
    adapter = MockModelAdapter()

    # Stream
    tokens = []
    async for chunk in adapter.stream(prompt="Test prompt for streaming"):
        tokens.append(chunk.text)
    assert len(tokens) > 0

    # Embeddings
    vecs = await adapter.embed(["Incident in Building A", "Incident in Building B"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 768


# ---------------------------------------------------------------------------
# 2. Policy Engine Invariant Tests
# ---------------------------------------------------------------------------

def test_policy_sec_001_tenant_boundary_denial():
    """Enforces rule SEC_001: Deny actions crossing campus boundaries."""
    proposal = ActionProposal(
        action_type="CREATE_TASK",
        target_campus_id="cmp_other_tenant",
        action_justification="Attempt cross-campus dispatch",
    )
    context = {
        "campus_id": "cmp_authorized_tenant",
        "category": "FACILITIES",
        "raw_text": "Cross-campus dispatch request",
    }
    eval_res = PolicyEngine.evaluate(proposal, context)
    assert eval_res.decision == "DENY"
    assert eval_res.rule_id == "SEC_001_TENANT_BOUNDARY"


def test_policy_saf_001_life_safety_human_gate():
    """Enforces rule SAF_001: Critical safety incidents require human supervisor approval."""
    proposal = ActionProposal(
        action_type="CREATE_TASK",
        priority="CRITICAL",
        target_campus_id="cmp_01",
    )
    context = {
        "campus_id": "cmp_01",
        "category": "SAFETY",
        "raw_text": "Chemical spill detected in Chemistry Lab",
    }
    eval_res = PolicyEngine.evaluate(proposal, context)
    assert eval_res.decision == "REQUIRE_HUMAN_APPROVAL"
    assert eval_res.rule_id == "SAF_001_LIFE_SAFETY"
    assert eval_res.required_approver_role == "SAFETY_OFFICER"


def test_policy_fin_001_cost_threshold_human_gate():
    """Enforces rule FIN_001: Operational actions exceeding $500 require budget approver."""
    proposal = ActionProposal(
        action_type="CREATE_TASK",
        priority="MEDIUM",
        estimated_cost=750.0,
        target_campus_id="cmp_01",
    )
    context = {
        "campus_id": "cmp_01",
        "category": "FACILITIES",
        "raw_text": "HVAC Chiller component replacement",
    }
    eval_res = PolicyEngine.evaluate(proposal, context)
    assert eval_res.decision == "REQUIRE_HUMAN_APPROVAL"
    assert eval_res.rule_id == "FIN_001_COST_LIMIT"
    assert eval_res.required_approver_role == "FACILITY_DIRECTOR"


def test_policy_ops_001_routine_dispatch_auto_allow():
    """Enforces rule OPS_001: Routine low-cost maintenance actions are auto-allowed."""
    proposal = ActionProposal(
        action_type="CREATE_TASK",
        priority="MEDIUM",
        estimated_cost=120.0,
        target_campus_id="cmp_01",
    )
    context = {
        "campus_id": "cmp_01",
        "category": "IT",
        "raw_text": "Ethernet cable replacement",
    }
    eval_res = PolicyEngine.evaluate(proposal, context)
    assert eval_res.decision == "ALLOW"
    assert eval_res.rule_id == "OPS_001_ROUTINE_DISPATCH"


# ---------------------------------------------------------------------------
# 3. Typed Tool Registry Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_registry_lists_all_11_contracts():
    """Validates that ToolRegistry exposes all 11 typed tool contracts."""
    registry = get_tool_registry()
    tools = registry.list_tools()
    tool_names = [t["name"] for t in tools]

    expected = [
        "get_location_context",
        "search_related_incidents",
        "search_policies",
        "get_department_capabilities",
        "calculate_priority",
        "create_incident_task",
        "assign_task",
        "send_notification",
        "request_human_approval",
        "escalate_incident",
        "record_resolution",
    ]
    for exp in expected:
        assert exp in tool_names, f"Missing tool registration for {exp}"


@pytest.mark.asyncio
async def test_tool_registry_schema_validation_failure():
    """Validates that passing invalid arguments fails cleanly with validation error."""
    registry = get_tool_registry()
    # get_location_context requires building_name, room_number, campus_id
    rec = await registry.execute(
        tool_name="get_location_context",
        arguments={"invalid_param": 123},
    )
    assert rec.status == "FAILED"
    assert "Schema validation error" in (rec.error or "")


@pytest.mark.asyncio
async def test_tool_registry_execution_and_telemetry():
    """Validates tool execution, output payload, and telemetry tracking."""
    registry = get_tool_registry()
    corrs = {"X-Request-ID": "req_test_01", "X-Trace-ID": "trace_test_01"}
    rec = await registry.execute(
        tool_name="calculate_priority",
        arguments={
            "category": "SAFETY",
            "student_count_affected": 80,
            "urgency_flag": True,
        },
        tenant_id="cmp_01",
        correlation_headers=corrs,
    )
    assert rec.status == "SUCCESS"
    assert rec.output.get("priority") == "CRITICAL"
    assert rec.duration_ms >= 0.0
    assert rec.tool_call_id.startswith("tool_")


# ---------------------------------------------------------------------------
# 4. LangGraph Stateful Orchestration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestration_routine_incident_success():
    """Validates end-to-end traversal of routine incident resulting in SUCCESS."""
    state = IncidentAgentState(
        incident_id=f"inc_{uuid.uuid4().hex[:8]}",
        organization_id="org_test",
        campus_id="cmp_main",
        raw_user_report="Whiteboard marker dry and projector remote missing in Room 204",
    )
    res = await orchestrate_incident(state)

    assert res["execution_status"] == "SUCCESS"
    assert res["policy"].decision == "ALLOW"
    assert "observe" in res["step_history"]
    assert "act" in res["step_history"]
    assert "monitor_resolve" in res["step_history"]
    assert len(res["executed_tools"]) >= 3
    assert "Successfully coordinated" in res["summary"]


@pytest.mark.asyncio
async def test_orchestration_human_approval_suspension_and_resume():
    """
    Validates that a critical/expensive incident halts at human_gate,
    and cleanly resumes upon explicit approval.
    """
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    state = IncidentAgentState(
        incident_id=thread_id,
        organization_id="org_test",
        campus_id="cmp_main",
        raw_user_report="Emergency: Smoke detected and HVAC chiller burning smell in Engineering Block",
    )

    # 1. First run suspends at human gate
    suspended_res = await orchestrate_incident(state, thread_id=thread_id)
    assert suspended_res["execution_status"] == "SUSPENDED"
    assert suspended_res["policy"].decision == "REQUIRE_HUMAN_APPROVAL"
    assert suspended_res["approval_id"] is not None
    assert suspended_res["current_node"] == "human_gate"

    # 2. Resume with approval
    resumed_res = await resume_orchestration(
        thread_id=thread_id,
        approval_status="APPROVED",
        approver_role="CAMPUS_DIRECTOR",
    )
    assert resumed_res["execution_status"] == "SUCCESS"
    assert resumed_res["approval_status"] == "APPROVED"
    assert "human_approved" in resumed_res["step_history"]
    assert "Successfully coordinated" in resumed_res["summary"]


@pytest.mark.asyncio
async def test_orchestration_human_rejection_marks_failed():
    """Validates that human rejection halts execution without tool dispatch."""
    thread_id = f"thread_rej_{uuid.uuid4().hex[:8]}"
    state = IncidentAgentState(
        incident_id=thread_id,
        organization_id="org_test",
        campus_id="cmp_main",
        raw_user_report="Emergency smoke and major HVAC fire hazard",
    )

    suspended_res = await orchestrate_incident(state, thread_id=thread_id)
    assert suspended_res["execution_status"] == "SUSPENDED"

    # Reject
    rejected_res = await resume_orchestration(
        thread_id=thread_id,
        approval_status="REJECTED",
        approver_role="CAMPUS_ADMIN",
        reason="False alarm reported by building security",
    )
    assert rejected_res["execution_status"] == "FAILED"
    assert rejected_res["approval_status"] == "REJECTED"
    assert "human_rejected" in rejected_res["step_history"]
    assert "False alarm" in rejected_res["summary"]


# ---------------------------------------------------------------------------
# 5. FastAPI Endpoints Integration Tests
# ---------------------------------------------------------------------------

def test_api_list_tools():
    """Validates GET /api/v1/tools endpoint."""
    client = TestClient(app)
    resp = client.get("/api/v1/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["data"]["count"] == 13


def test_api_execute_tool_directly():
    """Validates POST /api/v1/tools/execute."""
    client = TestClient(app)
    payload = {
        "tool_name": "calculate_priority",
        "arguments": {
            "category": "FACILITIES",
            "student_count_affected": 15,
            "urgency_flag": False,
        },
    }
    resp = client.post(
        "/api/v1/tools/execute",
        json=payload,
        headers={"X-Tenant-ID": "cmp_01", "X-Request-ID": "req_direct_01"},
    )
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["status"] == "success"
    assert res_json["data"]["tool_name"] == "calculate_priority"
    assert res_json["data"]["output"]["priority"] in ["LOW", "MEDIUM", "HIGH"]


def test_api_orchestrate_incident_success():
    """Validates POST /api/v1/orchestrate/incident."""
    client = TestClient(app)
    inc_id = f"inc_{uuid.uuid4().hex[:8]}"
    payload = {
        "incident_id": inc_id,
        "raw_user_report": "Water leak in Room 204 Engineering Block",
        "organization_id": "org_main",
        "campus_id": "cmp_engineering",
    }
    headers = {
        "X-Tenant-ID": "cmp_engineering",
        "X-Request-ID": "req_api_01",
        "X-Trace-ID": "trace_api_01",
    }
    resp = client.post("/api/v1/orchestrate/incident", json=payload, headers=headers)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["status"] == "success"
    data = res_json["data"]
    assert data["incident_id"] == inc_id
    assert data["execution_status"] in ["SUCCESS", "SUSPENDED"]
    assert "meta" in res_json
    assert res_json["meta"]["tenant_id"] == "cmp_engineering"


def test_api_orchestrate_missing_tenant_returns_400():
    """Enforces ADR-001: Missing tenant context yields 400 Bad Request."""
    client = TestClient(app)
    payload = {
        "incident_id": "inc_no_tenant",
        "raw_user_report": "Some incident without tenant",
    }
    resp = client.post("/api/v1/orchestrate/incident", json=payload)
    assert resp.status_code == 400
    assert "Tenant context required" in resp.json()["detail"]


def test_api_orchestrate_resume_flow():
    """Validates POST /api/v1/orchestrate/resume."""
    client = TestClient(app)
    inc_id = f"inc_suspend_{uuid.uuid4().hex[:8]}"
    payload = {
        "incident_id": inc_id,
        "raw_user_report": "Critical smoke and fire hazard in Basement",
        "campus_id": "cmp_engineering",
    }
    headers = {"X-Tenant-ID": "cmp_engineering"}

    # Suspend
    resp1 = client.post("/api/v1/orchestrate/incident", json=payload, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["data"]["execution_status"] == "SUSPENDED"

    # Resume
    resume_payload = {
        "thread_id": inc_id,
        "approval_status": "APPROVED",
        "approver_role": "CAMPUS_ADMIN",
    }
    resp2 = client.post("/api/v1/orchestrate/resume", json=resume_payload, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["data"]["execution_status"] == "SUCCESS"
