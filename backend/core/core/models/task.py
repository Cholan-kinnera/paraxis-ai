"""
Canonical Task & Dispatch management models for Paraxis AI Core Platform.
Turns reported incidents into executable, assigned, and SLA-bound operational work orders.
Adheres to ADR-003, ADR-006, and strict tenant and campus isolation invariants.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from core.models.base import TenantScopedModel, TenantScopedQuerySet, TenantScopedManager
from core.models.incident import IncidentPriority
from core.models.audit import ActorType


class TaskStatus(models.TextChoices):
    """
    Deterministic lifecycle states for an operational task.
    """
    PENDING = "PENDING", "Pending"
    ASSIGNED = "ASSIGNED", "Assigned"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    BLOCKED = "BLOCKED", "Blocked"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class TaskType(models.TextChoices):
    """
    Typed operational work categories for tasks.
    """
    INSPECTION = "INSPECTION", "Inspection & Diagnostics"
    REPAIR = "REPAIR", "Repair & Fix"
    MAINTENANCE = "MAINTENANCE", "Preventative Maintenance"
    COMMUNICATION = "COMMUNICATION", "Student/Faculty Communication"
    ESCALATION = "ESCALATION", "Administrative Escalation"
    FOLLOW_UP = "FOLLOW_UP", "Follow-up Verification"
    OTHER = "OTHER", "Other Operational Work"


class TaskEventType(models.TextChoices):
    """
    Event types for the durable append-only operational timeline of a task.
    """
    CREATED = "CREATED", "Task Created"
    ASSIGNED = "ASSIGNED", "Assigned"
    REASSIGNED = "REASSIGNED", "Reassigned"
    STARTED = "STARTED", "Work Started"
    BLOCKED = "BLOCKED", "Blocked"
    UNBLOCKED = "UNBLOCKED", "Unblocked"
    SLA_WARNING = "SLA_WARNING", "SLA At Risk Warning"
    SLA_BREACHED = "SLA_BREACHED", "SLA Deadline Breached"
    COMPLETED = "COMPLETED", "Task Completed"
    CANCELLED = "CANCELLED", "Task Cancelled"
    COMMENTED = "COMMENTED", "Comment Added"


VALID_TASK_TRANSITIONS = {
    TaskStatus.PENDING: {
        TaskStatus.ASSIGNED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.ASSIGNED: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.ASSIGNED,  # Reassignment
        TaskStatus.CANCELLED,
    },
    TaskStatus.IN_PROGRESS: {
        TaskStatus.BLOCKED,
        TaskStatus.COMPLETED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.BLOCKED: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.CANCELLED,
    },
    TaskStatus.COMPLETED: set(),  # Terminal state
    TaskStatus.CANCELLED: set(),  # Terminal state
}


# ============================================================================
# MANAGERS & IMMUTABILITY
# ============================================================================

class TaskQuerySet(TenantScopedQuerySet):
    """
    QuerySet for Task with soft-deletion support.
    """
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class TaskManager(TenantScopedManager.from_queryset(TaskQuerySet)):
    """
    Default manager for Task. Fails closed and filters out soft-deleted records.
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class TaskEventImmutableError(ValidationError):
    """Raised when an attempt is made to modify or delete an immutable task timeline event."""
    pass


class TaskEventQuerySet(TenantScopedQuerySet):
    """
    Immutable QuerySet for TaskEvent preventing in-place updates and bulk deletions.
    """
    def update(self, **kwargs):
        raise TaskEventImmutableError("Task timeline event records are immutable and cannot be updated.")

    def delete(self):
        raise TaskEventImmutableError("Task timeline event records are immutable and cannot be deleted.")


class TaskEventManager(TenantScopedManager.from_queryset(TaskEventQuerySet)):
    pass


# ============================================================================
# TASK MODEL
# ============================================================================

class Task(TenantScopedModel):
    """
    Canonical operational task / work order in Paraxis AI.
    Linked to an Incident, assigned to a technician or department, and governed by an SLA.
    """
    campus_scoped = True

    # Linked Parent Incident (PROTECT to prevent historical audit destruction)
    incident = models.ForeignKey(
        "core.Incident",
        on_delete=models.PROTECT,
        related_name="tasks",
        db_index=True,
        help_text="Parent operational incident that spawned this task",
    )

    # Core Task Content
    title = models.CharField(
        max_length=255,
        help_text="Clear, actionable title of the operational task",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed instructions or context for the assigned technician",
    )

    # Status, Priority & Categorization
    status = models.CharField(
        max_length=32,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        db_index=True,
        help_text="Current lifecycle state",
    )
    priority = models.CharField(
        max_length=32,
        choices=IncidentPriority.choices,
        default=IncidentPriority.MEDIUM,
        db_index=True,
        help_text="Operational urgency / priority",
    )
    task_type = models.CharField(
        max_length=50,
        choices=TaskType.choices,
        default=TaskType.OTHER,
        db_index=True,
        help_text="Typed category of work to be performed",
    )

    # Operational Assignment Boundaries
    assigned_user = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        db_index=True,
        help_text="Assigned operational technician / specialist",
    )
    assigned_department = models.ForeignKey(
        "core.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        db_index=True,
        help_text="Assigned campus service unit / department",
    )
    created_by = models.ForeignKey(
        "core.User",
        on_delete=models.PROTECT,
        related_name="created_tasks",
        help_text="User (admin, dispatcher, or system) who initiated this task",
    )

    # SLA Reference
    sla = models.ForeignKey(
        "core.SLA",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        help_text="Governing SLA policy applied to this task",
    )

    # Operational Timestamps
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Resolution deadline calculated by the SLA engine",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when technician initiated work (transition to IN_PROGRESS)",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when technician completed all required work",
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when task was cancelled before completion",
    )

    # Flexible metadata & soft deletion
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured operational telemetry, tool parameters, or checklist states",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp for soft-deletion",
    )

    # Managers
    objects = TaskManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "campus", "status"]),
            models.Index(fields=["incident", "status"]),
            models.Index(fields=["assigned_user", "status"]),
            models.Index(fields=["assigned_department", "status"]),
            models.Index(fields=["due_at", "status"]),
        ]

    def clean(self):
        super().clean()
        if not self.organization_id:
            raise ValidationError("Task must belong to an organization.")
        if not self.campus_id:
            raise ValidationError("Task must belong to a campus.")

        # 1. Validate Incident consistency (must match organization and campus)
        if self.incident_id:
            incident = self.incident
            if incident.organization_id != self.organization_id:
                raise ValidationError(
                    f"Incident organization ({incident.organization_id}) must match Task organization ({self.organization_id})."
                )
            if incident.campus_id != self.campus_id:
                raise ValidationError(
                    f"Incident campus ({incident.campus_id}) must match Task campus ({self.campus_id})."
                )

        # 2. Validate SLA consistency (must match organization and campus)
        if self.sla_id:
            sla = self.sla
            if sla.organization_id != self.organization_id:
                raise ValidationError(
                    f"SLA organization ({sla.organization_id}) must match Task organization ({self.organization_id})."
                )
            if sla.campus_id != self.campus_id:
                raise ValidationError(
                    f"SLA campus ({sla.campus_id}) must match Task campus ({self.campus_id})."
                )

        # 3. Validate Assigned User consistency
        if self.assigned_user_id:
            user = self.assigned_user
            if not user.is_active:
                raise ValidationError("Cannot assign task to an inactive user account.")
            if user.organization_id != self.organization_id:
                raise ValidationError("Cannot assign task to a user from a different organization.")
            if user.primary_campus_id and user.primary_campus_id != self.campus_id:
                raise ValidationError("Cannot assign task to a user whose primary campus does not match the task campus.")

        # 4. Validate Assigned Department consistency
        if self.assigned_department_id:
            dept = self.assigned_department
            if dept.organization_id != self.organization_id:
                raise ValidationError("Cannot assign task to a department from a different organization.")
            if dept.campus_id != self.campus_id:
                raise ValidationError("Cannot assign task to a department from a different campus.")

        # 5. Validate Created By consistency
        if self.created_by_id:
            creator = self.created_by
            if creator.organization_id != self.organization_id:
                raise ValidationError("Task creator must belong to the same organization.")

        # 6. Validate Lifecycle State Transitions
        if self.pk:
            try:
                current = Task.all_objects.get(pk=self.pk)
                if current.status != self.status:
                    allowed = VALID_TASK_TRANSITIONS.get(current.status, set())
                    if self.status not in allowed:
                        raise ValidationError(
                            f"Invalid state transition from '{current.status}' to '{self.status}'. Allowed transitions: {sorted(list(allowed))}."
                        )
            except Task.DoesNotExist:
                pass

    def soft_delete(self):
        """Soft-deletes the task by setting deleted_at."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def __str__(self):
        return f"[{self.status}] {self.title} (Incident: {self.incident_id})"


# ============================================================================
# TASK EVENT TIMELINE MODEL
# ============================================================================

class TaskEvent(TenantScopedModel):
    """
    Append-only, immutable operational timeline event for a Task.
    Tracks state transitions, assignments, SLA warnings/breaches, and comments.
    """
    campus_scoped = True

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="events",
        db_index=True,
        help_text="Task to which this timeline event belongs",
    )
    event_type = models.CharField(
        max_length=50,
        choices=TaskEventType.choices,
        db_index=True,
        help_text="Type of operational event",
    )
    actor = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this event (null if automated or system)",
    )
    actor_type = models.CharField(
        max_length=32,
        choices=ActorType.choices,
        default=ActorType.USER,
        help_text="Actor classification (USER, SYSTEM, or AGENT)",
    )
    from_status = models.CharField(
        max_length=32,
        blank=True,
        help_text="Previous task status before this event",
    )
    to_status = models.CharField(
        max_length=32,
        blank=True,
        help_text="New task status after this event",
    )
    message = models.TextField(
        blank=True,
        help_text="Human-readable description, notes, or resolution comments",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional structured event context",
    )

    # Managers
    objects = TaskEventManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "Task Event"
        verbose_name_plural = "Task Events"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def clean(self):
        super().clean()
        if self.task_id:
            task = self.task
            if task.organization_id != self.organization_id:
                raise ValidationError("TaskEvent organization must match Task organization.")
            if task.campus_id != self.campus_id:
                raise ValidationError("TaskEvent campus must match Task campus.")

    def save(self, *args, **kwargs):
        # Prevent in-place modifications to existing task events
        if self.pk:
            try:
                existing = TaskEvent.all_objects.filter(pk=self.pk).exists()
                if existing:
                    raise TaskEventImmutableError("Existing task timeline events cannot be modified.")
            except Exception:
                raise
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TaskEventImmutableError("Task timeline events are immutable and cannot be deleted.")

    def __str__(self):
        return f"[{self.event_type}] Task {self.task_id} at {self.created_at}"
