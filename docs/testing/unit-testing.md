# Unit Testing Standards — Paraxis AI

> **Purpose**: Guidelines, conventions, and mocking practices for unit tests across Python and TypeScript.

---

## 1. Python Unit Testing (`pytest`)

- **File Location**: Adjacent to tested modules in `tests/` directories or `test_*.py` files.
- **Rule of Isolation**: Unit tests must execute in-memory without spinning up external Docker databases or network servers.
- **Mocking External Services**:
  - LLM calls must use `MockModelAdapter`.
  - Database calls for pure domain logic should use in-memory fixtures.

### Example Unit Test (Policy Engine)
```python
import pytest
from backend.intelligence.agent.state import ActionProposal
from backend.intelligence.agent.nodes.policy_gate import DeterministicPolicyEngine

def test_policy_engine_gates_high_cost():
    action = ActionProposal(
        action_type="CREATE_TASK",
        department_id="dept_1",
        priority="MEDIUM",
        estimated_cost=1200.0,
        action_justification="Generator replacement"
    )
    context = {"current_campus_id": "camp_1", "campus_auto_spend_limit": 500.0}
    verdict = DeterministicPolicyEngine.evaluate(action, context)
    assert verdict.decision == "REQUIRE_HUMAN_APPROVAL"
    assert "exceeds auto-limit" in verdict.reason
```

---

## 2. Frontend Unit Testing (`Vitest`)

- **File Location**: `frontend/__tests__/**/*.test.tsx`
- Components are rendered using React Testing Library to assert accessibility attributes and proper DOM element presence.
