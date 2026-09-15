"""
Canonical SLA and SLA Tracking models for Paraxis AI Core Platform.
Provides deterministic operational target definitions and SLA tracking per task.
Adheres to ADR-003, ADR-006, and multi-tenant security invariants.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from core.models.base import TenantScopedModel
from core.models.incident import IncidentPriority, IncidentCategory


class SLAState(models.TextChoices):
    """
    Deterministic operational status of an active SLA instance.
    PAUSED is omitted for Phase 4 per specification.
    """
    HEALTHY = "HEALTHY", "Healthy"
    AT_RISK = "AT_RISK", "At Risk"
    BREACHED = "BREACHED", "Breached"
    MET = "MET", "Met"


class SLA(TenantScopedModel):
    """
    SLA policy target definitions scoped to an organization and campus.
    Defines response and resolution duration targets based on priority and task category.
    """
    campus_scoped = True

    name = models.CharField(
        max_length=100,
        help_text="Human-readable policy name (e.g. Critical Hardware Outage SLA)",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of SLA scope and operational terms",
    )
    priority = models.CharField(
        max_length=32,
        choices=IncidentPriority.choices,
        null=True,
        blank=True,
        db_index=True,
        help_text="Applicable incident/task priority level (None for universal)",
    )
    task_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="Applicable task type (None for universal)",
    )
    category = models.CharField(
        max_length=50,
        choices=IncidentCategory.choices,
        null=True,
        blank=True,
        db_index=True,
        help_text="Applicable operational domain category (None for universal)",
    )
    response_target = models.DurationField(
        help_text="Target duration to respond / begin work on the task",
    )
    resolution_target = models.DurationField(
        help_text="Target duration to complete the task work",
    )
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this SLA policy is actively applied to new tasks",
    )

    class Meta:
        verbose_name = "SLA"
        verbose_name_plural = "SLAs"
        ordering = ["priority", "resolution_target"]
        indexes = [
            models.Index(fields=["organization", "campus", "active"]),
            models.Index(fields=["priority", "category", "active"]),
        ]

    def clean(self):
        super().clean()
        if not self.organization_id:
            raise ValidationError("SLA must belong to an organization.")
        if not self.campus_id:
            raise ValidationError("SLA must belong to a campus.")

        if self.campus_id and self.campus.organization_id != self.organization_id:
            raise ValidationError("Campus must belong to the same organization as the SLA.")

        if self.response_target and self.resolution_target:
            if self.response_target > self.resolution_target:
                raise ValidationError("Response target duration cannot exceed resolution target duration.")

    def __str__(self):
        return f"{self.name} ({self.priority or 'All'} - Res: {self.resolution_target})"


class SLATracking(TenantScopedModel):
    """
    Operational SLA compliance tracking instance for an individual Task.
    Owns authoritative response and resolution due dates and deterministic breach detection.
    """
    campus_scoped = True

    task = models.OneToOneField(
        "core.Task",
        on_delete=models.CASCADE,
        related_name="sla_tracking",
        help_text="Task being monitored by this SLA tracking instance",
    )
    sla = models.ForeignKey(
        "core.SLA",
        on_delete=models.PROTECT,
        related_name="trackings",
        help_text="Authoritative SLA policy applied to this task",
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when SLA monitoring commenced",
    )
    response_due_at = models.DateTimeField(
        help_text="Authoritative deadline for response/acknowledgement",
    )
    resolution_due_at = models.DateTimeField(
        help_text="Authoritative deadline for task resolution/completion",
    )
    response_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when task response requirement was met (started work)",
    )
    resolution_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when task completion requirement was met",
    )
    response_breached_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when response deadline was breached",
    )
    resolution_breached_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when resolution deadline was breached",
    )
    state = models.CharField(
        max_length=32,
        choices=SLAState.choices,
        default=SLAState.HEALTHY,
        db_index=True,
        help_text="Current deterministic SLA compliance status",
    )

    class Meta:
        verbose_name = "SLA Tracking"
        verbose_name_plural = "SLA Trackings"
        indexes = [
            models.Index(fields=["organization", "campus", "state"]),
            models.Index(fields=["resolution_due_at", "state"]),
        ]

    def clean(self):
        super().clean()
        if self.task_id:
            task = self.task
            # Organization & campus consistency across Task and SLA
            if task.organization_id != self.organization_id:
                raise ValidationError("SLATracking organization must match the task organization.")
            if task.campus_id != self.campus_id:
                raise ValidationError("SLATracking campus must match the task campus.")

            if self.sla_id:
                sla = self.sla
                if sla.organization_id != self.organization_id:
                    raise ValidationError("Applied SLA organization must match the task organization.")
                if sla.campus_id != self.campus_id:
                    raise ValidationError("Applied SLA campus must match the task campus.")

    def __str__(self):
        return f"SLA Tracking for Task {self.task_id} [{self.state}]"
