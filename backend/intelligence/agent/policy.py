"""
Deterministic Policy Engine for Paraxis AI.
Enforces the safety gating boundary between AI proposals and physical tool executions.
Adheres to ADR-005 and docs/agents/policy-engine.md.
"""
from typing import Dict, Any, Optional
from backend.intelligence.agent.state import ActionProposal, PolicyEvaluation

DEFAULT_AUTO_SPEND_LIMIT = 500.0


class PolicyEngine:
    """
    Deterministic rules engine.
    Guarantees LLM proposals never cause unauthorized real-world side effects.
    """

    @classmethod
    def evaluate(
        cls,
        proposal: ActionProposal,
        context: Dict[str, Any],
        auto_spend_limit: float = DEFAULT_AUTO_SPEND_LIMIT,
    ) -> PolicyEvaluation:
        current_campus_id = context.get("campus_id")
        target_campus_id = proposal.target_campus_id or current_campus_id

        # 1. Hard Tenant Boundary Gate
        if current_campus_id and target_campus_id and target_campus_id != current_campus_id:
            return PolicyEvaluation(
                decision="DENY",
                rule_id="SEC_001_TENANT_BOUNDARY",
                reason=f"Action attempted cross-tenant campus execution ({target_campus_id} != {current_campus_id}).",
            )

        # 2. Immutable Audit Gate
        action_type_lower = (proposal.action_type or "").lower()
        if "audit" in action_type_lower or "delete_audit" in action_type_lower:
            return PolicyEvaluation(
                decision="DENY",
                rule_id="SEC_002_IMMUTABLE_AUDIT",
                reason="Direct alteration of immutable audit trails is prohibited.",
            )

        # 3. Emergency & Life-Safety Gate
        is_life_safety = context.get("is_life_safety_concern", False)
        if is_life_safety or proposal.priority == "CRITICAL":
            return PolicyEvaluation(
                decision="REQUIRE_HUMAN_APPROVAL",
                rule_id="SAF_001_LIFE_SAFETY",
                reason="Critical safety hazards or priority CRITICAL actions require verification by Safety Officer.",
                required_approver_role="SAFETY_OFFICER",
            )

        # 4. Financial Spending Limit Gate
        spend_limit = context.get("campus_auto_spend_limit", auto_spend_limit)
        if proposal.estimated_cost > spend_limit:
            return PolicyEvaluation(
                decision="REQUIRE_HUMAN_APPROVAL",
                rule_id="FIN_001_COST_LIMIT",
                reason=f"Estimated cost (${proposal.estimated_cost:.2f}) exceeds autonomous spend limit of ${spend_limit:.2f}.",
                required_approver_role="FACILITY_DIRECTOR",
            )

        # 5. Mass Communication Gate
        if proposal.action_type == "BROADCAST_NOTIFICATION" or context.get("is_campus_wide_broadcast"):
            return PolicyEvaluation(
                decision="REQUIRE_HUMAN_APPROVAL",
                rule_id="PUB_001_MASS_BROADCAST",
                reason="Campus-wide broadcast announcements require administrative sign-off.",
                required_approver_role="CAMPUS_ADMIN",
            )

        # 6. Standard Routine Dispatch Gate
        return PolicyEvaluation(
            decision="ALLOW",
            rule_id="OPS_001_ROUTINE_DISPATCH",
            reason="Action conforms to standard operational dispatch policies.",
            required_approver_role=None,
        )
