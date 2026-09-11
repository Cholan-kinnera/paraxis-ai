# Policy Engine Specification — Paraxis AI

> **Purpose**: Deterministic rules engine intercepting all proposed agent actions. Guarantees that LLM outputs never directly cause unauthorized real-world side effects.

---

## 1. Decision States

The Policy Engine returns exactly one of three immutable verdicts for every proposed action:

1. **`ALLOW`**: The action satisfies all pre-approved criteria for routine operations. The system executes immediately without human blockage.
2. **`REQUIRE_HUMAN_APPROVAL`**: The action carries significant financial, legal, disciplinary, or safety consequences. Execution halts until an authorized human signs off.
3. **`DENY`**: The action violates a hard constraint (e.g., unauthorized cross-campus access, illegal data alteration). The action is dropped, and a security alert is recorded.

---

## 2. Action Governance Matrix

| Proposed Action | Parameters / Context | Policy Verdict | Justification / Rule |
| :--- | :--- | :--- | :--- |
| `get_location_context` | Any valid room query within active campus | `ALLOW` | Safe, read-only operational context. |
| `search_related_incidents` | Query scoped to tenant campus | `ALLOW` | Safe, read-only duplicate analysis. |
| `create_incident_task` | Routine repair (Cost <= $500, Priority LOW/MED/HIGH) | `ALLOW` | Standard maintenance dispatch. |
| `create_incident_task` | High-cost repair (Estimated cost > $500) | `REQUIRE_HUMAN_APPROVAL` | Financial spending limit exceeded. Requires Facility Director sign-off. |
| `create_incident_task` | Critical Safety Hazard (e.g., gas leak, fire) | `REQUIRE_HUMAN_APPROVAL` | Immediate Safety Officer oversight required. |
| `assign_task` | Assign to qualified on-duty technician | `ALLOW` | Routine operational assignment. |
| `send_notification` | Routine status update to reporter | `ALLOW` | Transparent student feedback. |
| `send_notification` | Campus-wide broadcast notice | `REQUIRE_HUMAN_APPROVAL` | Mass communications require Dean/Director authorization. |
| *Any Action* | Requesting access to a different `campus_id` | `DENY` | Tenant boundary violation. |
| *Any Action* | Requesting modification to `AuditLog` | `DENY` | Immutable audit violation. |

---

## 3. Policy Rule Evaluation Logic

```python
class CampusPolicyRule:
    rule_id: str
    action_type: str
    condition_fn: callable
    verdict: str  # ALLOW, DENY, REQUIRE_HUMAN_APPROVAL
    required_role: Optional[str]
    description: str

def evaluate_proposed_action(action: ProposedAction, context: Dict[str, Any]) -> PolicyEvaluation:
    # 1. Hard Tenant Isolation Check
    if action.target_campus_id != context["current_campus_id"]:
        return PolicyEvaluation(
            decision="DENY",
            rule_id="SEC_001_TENANT_BOUNDARY",
            reason="Action attempted cross-tenant campus mutation"
        )
        
    # 2. Financial Threshold Gate
    if action.estimated_cost > context["campus_auto_spend_limit"]: # Default $500
        return PolicyEvaluation(
            decision="REQUIRE_HUMAN_APPROVAL",
            rule_id="FIN_001_COST_LIMIT",
            reason=f"Estimated cost ${action.estimated_cost} exceeds auto-limit of ${context['campus_auto_spend_limit']}",
            required_approver_role="FACILITY_DIRECTOR"
        )
        
    # 3. Emergency / Safety Gate
    if context.get("is_life_safety_concern") or action.priority == "CRITICAL":
        return PolicyEvaluation(
            decision="REQUIRE_HUMAN_APPROVAL",
            rule_id="SAF_001_LIFE_SAFETY",
            reason="Critical safety hazards require physical verification by Safety Officer",
            required_approver_role="SAFETY_OFFICER"
        )
        
    # 4. Standard Allowed Dispatch
    return PolicyEvaluation(
        decision="ALLOW",
        rule_id="OPS_001_ROUTINE_DISPATCH",
        reason="Action conforms to standard operational dispatch rules"
    )
```
