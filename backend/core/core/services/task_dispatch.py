"""
Task Dispatch & Lifecycle Domain Service for Paraxis AI Core Platform.
Coordinates task creation from incidents, operational assignment, state transitions,
SLA tracking attachment, and immutable timeline event logging.
Adheres to ADR-003, ADR-006, and system-of-record invariants.
"""
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models.incident import Incident
from core.models.task import Task, TaskEvent, TaskStatus, TaskType, TaskEventType
from core.models.user import User
from core.models.campus_graph import Department
from core.models.audit import ActorType
from core.services.audit import log_audit_event
from core.services.sla import attach_sla_to_task, evaluate_sla_state


@transaction.atomic
def create_task_from_incident(
    incident: Incident,
    title: str,
    description: str = "",
    task_type: str = TaskType.OTHER,
    priority: Optional[str] = None,
    assigned_user: Optional[User] = None,
    assigned_department: Optional[Department] = None,
    created_by: Optional[User] = None,
    actor: Optional[User] = None,
    metadata: Optional[dict] = None,
    request=None,
) -> Task:
    """
    Creates an operational task from a campus incident.
    Validates tenant scoping, initializes status, attaches applicable SLA,
    and records immutable TaskEvent and AuditLog entries.
    """
    if not incident:
        raise ValidationError("Incident is required to create a task.")

    creator = created_by or actor
    if not creator:
        raise ValidationError("Task creator is required.")

    initial_status = TaskStatus.PENDING
    if assigned_user or assigned_department:
        initial_status = TaskStatus.ASSIGNED

    task = Task(
        organization=incident.organization,
        campus=incident.campus,
        incident=incident,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority or incident.priority,
        status=initial_status,
        assigned_user=assigned_user,
        assigned_department=assigned_department,
        created_by=creator,
        metadata=metadata or {},
    )
    task.full_clean()
    task.save()

    # Attach governing SLA and compute deadlines
    attach_sla_to_task(task)

    # Record initial creation event
    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=TaskEventType.CREATED,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status="",
        to_status=task.status,
        message=f"Task '{task.title}' created for incident {incident.id}.",
        metadata={"incident_id": str(incident.id), "task_type": task.task_type},
    )

    if initial_status == TaskStatus.ASSIGNED:
        assignee_name = (
            assigned_user.full_name or assigned_user.email
            if assigned_user
            else assigned_department.name
        )
        TaskEvent.all_objects.create(
            organization=task.organization,
            campus=task.campus,
            task=task,
            event_type=TaskEventType.ASSIGNED,
            actor=actor,
            actor_type=ActorType.USER if actor else ActorType.SYSTEM,
            from_status=TaskStatus.PENDING,
            to_status=TaskStatus.ASSIGNED,
            message=f"Task assigned to {assignee_name}.",
        )

    log_audit_event(
        action="task.create",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        post_state={"status": task.status, "incident_id": str(incident.id)},
        request=request,
    )

    return task


@transaction.atomic
def assign_task(
    task: Task,
    assigned_user: Optional[User] = None,
    assigned_department: Optional[Department] = None,
    actor: Optional[User] = None,
    request=None,
) -> Task:
    """
    Assigns or reassigns an operational task to a technician or department.
    Enforces tenant/campus isolation and valid lifecycle transition to ASSIGNED.
    """
    if not assigned_user and not assigned_department:
        raise ValidationError("Either assigned_user or assigned_department must be specified.")

    old_status = task.status
    old_assigned_user = task.assigned_user
    old_assigned_dept = task.assigned_department

    task.assigned_user = assigned_user
    task.assigned_department = assigned_department
    task.status = TaskStatus.ASSIGNED

    task.full_clean()
    task.save(update_fields=["assigned_user", "assigned_department", "status", "updated_at"])

    event_type = (
        TaskEventType.REASSIGNED
        if old_status == TaskStatus.ASSIGNED
        else TaskEventType.ASSIGNED
    )
    assignee_desc = (
        assigned_user.full_name or assigned_user.email
        if assigned_user
        else assigned_department.name
    )

    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=event_type,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status=old_status,
        to_status=TaskStatus.ASSIGNED,
        message=f"Task assigned to {assignee_desc}.",
        metadata={
            "assigned_user_id": str(assigned_user.id) if assigned_user else None,
            "assigned_department_id": str(assigned_department.id) if assigned_department else None,
        },
    )

    log_audit_event(
        action="task.assign",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        pre_state={
            "assigned_user_id": str(old_assigned_user.id) if old_assigned_user else None,
            "assigned_department_id": str(old_assigned_dept.id) if old_assigned_dept else None,
            "status": old_status,
        },
        post_state={
            "assigned_user_id": str(assigned_user.id) if assigned_user else None,
            "assigned_department_id": str(assigned_department.id) if assigned_department else None,
            "status": task.status,
        },
        request=request,
    )

    return task


@transaction.atomic
def start_task(
    task: Task,
    actor: Optional[User] = None,
    request=None,
) -> Task:
    """
    Transitions task to IN_PROGRESS, sets started_at timestamp, and records SLA response completion.
    """
    old_status = task.status
    now = timezone.now()

    task.status = TaskStatus.IN_PROGRESS
    if not task.started_at:
        task.started_at = now

    task.full_clean()
    task.save(update_fields=["status", "started_at", "updated_at"])

    # Update SLA tracking response completion
    tracking = getattr(task, "sla_tracking", None)
    if tracking and not tracking.response_completed_at:
        tracking.response_completed_at = now
        tracking.save(update_fields=["response_completed_at", "updated_at"])

    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=TaskEventType.STARTED,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status=old_status,
        to_status=TaskStatus.IN_PROGRESS,
        message="Work initiated on task.",
    )

    log_audit_event(
        action="task.start",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        pre_state={"status": old_status},
        post_state={"status": task.status, "started_at": task.started_at.isoformat()},
        request=request,
    )

    return task


@transaction.atomic
def block_task(
    task: Task,
    reason: str,
    actor: Optional[User] = None,
    request=None,
) -> Task:
    """
    Transitions task to BLOCKED status with operational reason.
    """
    old_status = task.status
    task.status = TaskStatus.BLOCKED

    task.full_clean()
    task.save(update_fields=["status", "updated_at"])

    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=TaskEventType.BLOCKED,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status=old_status,
        to_status=TaskStatus.BLOCKED,
        message=f"Task blocked: {reason}",
        metadata={"reason": reason},
    )

    log_audit_event(
        action="task.block",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        pre_state={"status": old_status},
        post_state={"status": task.status, "reason": reason},
        request=request,
    )

    return task


@transaction.atomic
def unblock_task(
    task: Task,
    actor: Optional[User] = None,
    request=None,
) -> Task:
    """
    Transitions blocked task back to IN_PROGRESS status.
    """
    old_status = task.status
    task.status = TaskStatus.IN_PROGRESS

    task.full_clean()
    task.save(update_fields=["status", "updated_at"])

    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=TaskEventType.UNBLOCKED,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status=old_status,
        to_status=TaskStatus.IN_PROGRESS,
        message="Task unblocked and returned to active progress.",
    )

    log_audit_event(
        action="task.unblock",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        pre_state={"status": old_status},
        post_state={"status": task.status},
        request=request,
    )

    return task


@transaction.atomic
def complete_task(
    task: Task,
    resolution_notes: str = "",
    actor: Optional[User] = None,
    request=None,
) -> Task:
    """
    Transitions task to COMPLETED status and records resolution timestamp.
    Does NOT automatically resolve parent incident (Incident remains authoritative).
    """
    old_status = task.status
    now = timezone.now()

    task.status = TaskStatus.COMPLETED
    task.completed_at = now

    task.full_clean()
    task.save(update_fields=["status", "completed_at", "updated_at"])

    # Update SLA tracking resolution completion
    tracking = getattr(task, "sla_tracking", None)
    if tracking:
        tracking.resolution_completed_at = now
        tracking.state = evaluate_sla_state(tracking, current_time=now)
        tracking.save(update_fields=["resolution_completed_at", "state", "updated_at"])

    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=TaskEventType.COMPLETED,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status=old_status,
        to_status=TaskStatus.COMPLETED,
        message=resolution_notes or "Task work completed successfully.",
        metadata={"completed_at": now.isoformat()},
    )

    log_audit_event(
        action="task.complete",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        pre_state={"status": old_status},
        post_state={"status": task.status, "completed_at": now.isoformat()},
        request=request,
    )

    return task


@transaction.atomic
def cancel_task(
    task: Task,
    reason: str = "",
    actor: Optional[User] = None,
    request=None,
) -> Task:
    """
    Transitions task to CANCELLED terminal state.
    """
    old_status = task.status
    now = timezone.now()

    task.status = TaskStatus.CANCELLED
    task.cancelled_at = now

    task.full_clean()
    task.save(update_fields=["status", "cancelled_at", "updated_at"])

    TaskEvent.all_objects.create(
        organization=task.organization,
        campus=task.campus,
        task=task,
        event_type=TaskEventType.CANCELLED,
        actor=actor,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        from_status=old_status,
        to_status=TaskStatus.CANCELLED,
        message=f"Task cancelled: {reason}" if reason else "Task cancelled.",
        metadata={"reason": reason, "cancelled_at": now.isoformat()},
    )

    log_audit_event(
        action="task.cancel",
        entity_type="task",
        entity_id=str(task.id),
        actor=actor,
        organization=task.organization,
        campus=task.campus,
        pre_state={"status": old_status},
        post_state={"status": task.status, "cancelled_at": now.isoformat(), "reason": reason},
        request=request,
    )

    return task
