"""
Authoritative SLA Engine Service for Paraxis AI Core Platform.
Calculates deadlines, resolves applicable policies, and evaluates deterministic compliance states.
Adheres to ADR-003, ADR-006, and system-of-record invariants.
"""
from typing import Optional
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models.sla import SLA, SLATracking, SLAState
from core.models.task import Task, TaskEvent, TaskEventType
from core.models.audit import ActorType


def find_applicable_sla(
    organization_id,
    campus_id,
    priority: str,
    task_type: Optional[str] = None,
    category: Optional[str] = None,
) -> Optional[SLA]:
    """
    Deterministically resolves the most specific active SLA policy for a task.
    Priority hierarchy:
    1. Exact match on priority, task_type, and category
    2. Match on priority and task_type
    3. Match on priority and category
    4. Match on priority only
    5. Universal active fallback SLA
    """
    base_qs = SLA.all_objects.filter(
        organization_id=organization_id,
        campus_id=campus_id,
        active=True,
    )

    # 1. Exact match on priority, task_type, and category
    if task_type and category:
        match = base_qs.filter(priority=priority, task_type=task_type, category=category).first()
        if match:
            return match

    # 2. Match on priority and task_type
    if task_type:
        match = base_qs.filter(priority=priority, task_type=task_type, category__isnull=True).first()
        if match:
            return match

    # 3. Match on priority and category
    if category:
        match = base_qs.filter(priority=priority, category=category, task_type__isnull=True).first()
        if match:
            return match

    # 4. Match on priority only
    match = base_qs.filter(priority=priority, task_type__isnull=True, category__isnull=True).first()
    if match:
        return match

    # 5. Universal active fallback SLA
    match = base_qs.filter(priority__isnull=True, task_type__isnull=True, category__isnull=True).first()
    return match


def attach_sla_to_task(
    task: Task,
    sla: Optional[SLA] = None,
    started_at: Optional[datetime] = None,
) -> Optional[SLATracking]:
    """
    Attaches an applicable SLA to a task, computes deadlines, and persists SLATracking.
    """
    now = started_at or timezone.now()

    if sla:
        if sla.organization_id != task.organization_id:
            raise ValidationError("SLA organization does not match Task organization.")
        if sla.campus_id != task.campus_id:
            raise ValidationError("SLA campus does not match Task campus.")

    if not sla:
        sla = find_applicable_sla(
            organization_id=task.organization_id,
            campus_id=task.campus_id,
            priority=task.priority,
            task_type=task.task_type,
            category=getattr(task.incident, "category", None),
        )

    if not sla:
        return None

    if sla.organization_id != task.organization_id or sla.campus_id != task.campus_id:
        raise ValidationError("SLA organization and campus must match Task organization and campus.")

    response_due_at = now + sla.response_target
    resolution_due_at = now + sla.resolution_target

    # Update task due date and SLA link
    task.sla = sla
    task.due_at = resolution_due_at
    task.save(update_fields=["sla", "due_at", "updated_at"])

    # Create or update SLATracking instance
    tracking, _ = SLATracking.all_objects.update_or_create(
        task=task,
        defaults={
            "organization": task.organization,
            "campus": task.campus,
            "sla": sla,
            "started_at": now,
            "response_due_at": response_due_at,
            "resolution_due_at": resolution_due_at,
            "state": SLAState.HEALTHY,
        },
    )
    return tracking


def evaluate_sla_state(
    tracking: SLATracking,
    current_time: Optional[datetime] = None,
) -> str:
    """
    Deterministically computes current SLAState:
    - MET: Resolution was completed on or before the resolution deadline.
    - BREACHED: Current time has passed resolution due date, or response was missed.
    - AT_RISK: Remaining time <= 25% of the total target duration.
    - HEALTHY: Ample time remaining (>25%).
    """
    now = current_time or timezone.now()

    # 1. Check if already completed
    if tracking.resolution_completed_at:
        if tracking.resolution_completed_at <= tracking.resolution_due_at:
            return SLAState.MET
        return SLAState.BREACHED

    # 2. Check if resolution deadline is breached
    if now > tracking.resolution_due_at:
        return SLAState.BREACHED

    # 3. Check if response deadline was breached (if not yet responded to)
    if not tracking.response_completed_at and now > tracking.response_due_at:
        return SLAState.BREACHED

    # 4. Check AT_RISK threshold (remaining time <= 25% of total resolution target)
    total_duration = (tracking.resolution_due_at - tracking.started_at).total_seconds()
    remaining_duration = (tracking.resolution_due_at - now).total_seconds()

    if total_duration > 0 and (remaining_duration / total_duration) <= 0.25:
        return SLAState.AT_RISK

    return SLAState.HEALTHY


def check_and_record_breaches(
    task: Task,
    current_time: Optional[datetime] = None,
) -> Optional[str]:
    """
    Evaluates active SLA compliance for a task and records breaches or warnings if states change.
    """
    tracking = getattr(task, "sla_tracking", None)
    if not tracking:
        return None

    now = current_time or timezone.now()
    prev_state = tracking.state
    new_state = evaluate_sla_state(tracking, current_time=now)

    tracking.state = new_state
    update_fields = ["state", "updated_at"]

    # Record breach timestamps
    if new_state == SLAState.BREACHED and prev_state != SLAState.BREACHED:
        if now > tracking.resolution_due_at and not tracking.resolution_breached_at:
            tracking.resolution_breached_at = now
            update_fields.append("resolution_breached_at")
        elif not tracking.response_completed_at and now > tracking.response_due_at and not tracking.response_breached_at:
            tracking.response_breached_at = now
            update_fields.append("response_breached_at")

        # Emit immutable SLA_BREACHED task event
        TaskEvent.all_objects.create(
            organization=task.organization,
            campus=task.campus,
            task=task,
            event_type=TaskEventType.SLA_BREACHED,
            actor_type=ActorType.SYSTEM,
            from_status=task.status,
            to_status=task.status,
            message=f"SLA deadline breached for task '{task.title}'.",
            metadata={
                "sla_name": tracking.sla.name,
                "response_due_at": tracking.response_due_at.isoformat(),
                "resolution_due_at": tracking.resolution_due_at.isoformat(),
            },
        )
    elif new_state == SLAState.AT_RISK and prev_state == SLAState.HEALTHY:
        # Emit immutable SLA_WARNING task event
        TaskEvent.all_objects.create(
            organization=task.organization,
            campus=task.campus,
            task=task,
            event_type=TaskEventType.SLA_WARNING,
            actor_type=ActorType.SYSTEM,
            from_status=task.status,
            to_status=task.status,
            message=f"SLA remaining time is under 25% for task '{task.title}'.",
            metadata={
                "sla_name": tracking.sla.name,
                "resolution_due_at": tracking.resolution_due_at.isoformat(),
            },
        )

    tracking.save(update_fields=update_fields)
    return new_state
