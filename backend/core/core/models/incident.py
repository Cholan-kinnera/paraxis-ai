"""
Canonical Incident & Issue Management models for Paraxis AI.
Represents operational campus problems, location references in the Campus Operational Graph,
lifecycle state machine, and immutable incident timeline events.
Adheres to ADR-003, ADR-006, ADR-007, data-architecture.md, and domain-architecture.md.
"""
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from core.models.base import TenantScopedModel, TenantScopedQuerySet, TenantScopedManager
from core.models.audit import ActorType


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class IncidentStatus(models.TextChoices):
    """
    Lifecycle states for an operational incident as specified in low-level-design.md.
    """
    INGESTED = "INGESTED", "Ingested"
    TRIAGING = "TRIAGING", "Triaging"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    ASSIGNED = "ASSIGNED", "Assigned"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    ESCALATED = "ESCALATED", "Escalated"
    RESOLVED = "RESOLVED", "Resolved"
    VERIFIED = "VERIFIED", "Verified"
    CLOSED = "CLOSED", "Closed"
    REOPENED = "REOPENED", "Reopened"
    REJECTED = "REJECTED", "Rejected"
    DUPLICATE_LINKED = "DUPLICATE_LINKED", "Duplicate Linked"


class IncidentPriority(models.TextChoices):
    """
    Standard priority / severity levels for campus operational incidents.
    """
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class IncidentCategory(models.TextChoices):
    """
    Domain categories for campus operations and facilities.
    """
    IT_NETWORK = "IT_NETWORK", "IT & Networking"
    ELECTRICAL = "ELECTRICAL", "Electrical & Power"
    PLUMBING = "PLUMBING", "Plumbing & Sanitation"
    HVAC = "HVAC", "HVAC & Climate"
    SAFETY = "SAFETY", "Safety & Security"
    FACILITY = "FACILITY", "Facilities & Infrastructure"
    OTHER = "OTHER", "Other / General"


class IncidentSource(models.TextChoices):
    """
    Ingestion channel for the incident report.
    """
    WEB = "WEB", "Web Portal"
    MOBILE = "MOBILE", "Mobile App"
    KIOSK = "KIOSK", "Campus Kiosk"
    API = "API", "External API"
    SYSTEM = "SYSTEM", "System Automated"


class IncidentEventType(models.TextChoices):
    """
    Event types for the durable operational timeline of an incident.
    """
    REPORTED = "REPORTED", "Reported"
    STATUS_CHANGED = "STATUS_CHANGED", "Status Changed"
    PRIORITY_CHANGED = "PRIORITY_CHANGED", "Priority Changed"
    CATEGORY_CHANGED = "CATEGORY_CHANGED", "Category Changed"
    ASSIGNMENT_CHANGED = "ASSIGNMENT_CHANGED", "Assignment Changed"
    LOCATION_CHANGED = "LOCATION_CHANGED", "Location Changed"
    DUPLICATE_MARKED = "DUPLICATE_MARKED", "Marked as Duplicate"
    RESOLVED = "RESOLVED", "Resolved"
    VERIFIED = "VERIFIED", "Verified"
    REOPENED = "REOPENED", "Reopened"
    CLOSED = "CLOSED", "Closed"
    COMMENT_ADDED = "COMMENT_ADDED", "Comment Added"


# Valid state transitions dictionary (LLD Section 2)
VALID_TRANSITIONS = {
    IncidentStatus.INGESTED: {
        IncidentStatus.TRIAGING,
        IncidentStatus.ASSIGNED,
        IncidentStatus.PENDING_APPROVAL,
        IncidentStatus.DUPLICATE_LINKED,
        IncidentStatus.REJECTED,
        IncidentStatus.IN_PROGRESS,
    },
    IncidentStatus.TRIAGING: {
        IncidentStatus.ASSIGNED,
        IncidentStatus.PENDING_APPROVAL,
        IncidentStatus.DUPLICATE_LINKED,
        IncidentStatus.REJECTED,
        IncidentStatus.IN_PROGRESS,
    },
    IncidentStatus.PENDING_APPROVAL: {
        IncidentStatus.ASSIGNED,
        IncidentStatus.REJECTED,
    },
    IncidentStatus.ASSIGNED: {
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.ESCALATED,
        IncidentStatus.ASSIGNED,
        IncidentStatus.RESOLVED,
        IncidentStatus.REJECTED,
    },
    IncidentStatus.IN_PROGRESS: {
        IncidentStatus.RESOLVED,
        IncidentStatus.ESCALATED,
        IncidentStatus.ASSIGNED,
        IncidentStatus.REJECTED,
    },
    IncidentStatus.ESCALATED: {
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.ASSIGNED,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.VERIFIED,
        IncidentStatus.REOPENED,
        IncidentStatus.CLOSED,
    },
    IncidentStatus.VERIFIED: {
        IncidentStatus.CLOSED,
        IncidentStatus.REOPENED,
    },
    IncidentStatus.REOPENED: {
        IncidentStatus.ASSIGNED,
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.ESCALATED,
    },
    IncidentStatus.REJECTED: {
        IncidentStatus.CLOSED,
        IncidentStatus.REOPENED,
    },
    IncidentStatus.DUPLICATE_LINKED: {
        IncidentStatus.CLOSED,
        IncidentStatus.INGESTED,
    },
    IncidentStatus.CLOSED: {
        IncidentStatus.REOPENED,
    },
}


# ============================================================================
# MANAGERS & QUERYSETS
# ============================================================================

class IncidentQuerySet(TenantScopedQuerySet):
    """
    Queryset for Incident with soft-deletion and tenant scoping helpers.
    """
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class IncidentManager(TenantScopedManager.from_queryset(IncidentQuerySet)):
    """
    Default manager for Incident. Fails closed and filters out soft-deleted records.
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class IncidentEventImmutableError(ValidationError):
    """Raised when an attempt is made to modify or delete an immutable incident event."""
    pass


class IncidentEventQuerySet(TenantScopedQuerySet):
    """
    Immutable QuerySet for IncidentEvent preventing bulk update and delete.
    """
    def update(self, **kwargs):
        raise IncidentEventImmutableError("Incident event records are immutable and cannot be updated.")

    def delete(self):
        raise IncidentEventImmutableError("Incident event records are immutable and cannot be deleted.")


class IncidentEventManager(TenantScopedManager.from_queryset(IncidentEventQuerySet)):
    pass


# ============================================================================
# DOMAIN MODELS
# ============================================================================

class Incident(TenantScopedModel):
    """
    Canonical operational incident or issue reported on a campus.
    Owns operational lifecycle state, priority, and location in the Campus Operational Graph.
    """
    campus_scoped = True

    # Reporter
    reporter = models.ForeignKey(
        "core.User",
        on_delete=models.PROTECT,
        related_name="reported_incidents",
        db_index=True,
        help_text="User who reported the incident",
    )

    # Core Content
    title = models.CharField(
        max_length=255,
        help_text="Brief summary of the issue",
    )
    description = models.TextField(
        help_text="Detailed description of the incident / issue",
    )

    # Classification & Priority
    category = models.CharField(
        max_length=50,
        choices=IncidentCategory.choices,
        default=IncidentCategory.OTHER,
        db_index=True,
        help_text="Functional operational category",
    )
    priority = models.CharField(
        max_length=32,
        choices=IncidentPriority.choices,
        default=IncidentPriority.MEDIUM,
        db_index=True,
        help_text="Operational priority / urgency",
    )
    status = models.CharField(
        max_length=32,
        choices=IncidentStatus.choices,
        default=IncidentStatus.INGESTED,
        db_index=True,
        help_text="Current lifecycle state",
    )
    source = models.CharField(
        max_length=32,
        choices=IncidentSource.choices,
        default=IncidentSource.WEB,
        help_text="Ingestion channel",
    )

    # Assignment Boundary (Phase 3 scope: functional department & assigned user)
    department = models.ForeignKey(
        "core.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
        db_index=True,
        help_text="Responsible functional department (e.g. IT, Facilities)",
    )
    assigned_to = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_incidents",
        db_index=True,
        help_text="Assigned staff member / handler",
    )

    # Campus Operational Graph Location References
    building = models.ForeignKey(
        "core.Building",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
        db_index=True,
        help_text="Building where the issue occurred",
    )
    floor = models.ForeignKey(
        "core.Floor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
        db_index=True,
        help_text="Floor level where the issue occurred",
    )
    room = models.ForeignKey(
        "core.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
        db_index=True,
        help_text="Room / space where the issue occurred",
    )
    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
        db_index=True,
        help_text="Specific equipment / asset impacted",
    )

    # Duplicate Clustering Reference
    is_duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
        help_text="Master incident if this report is a confirmed duplicate",
    )

    # Resolution Details
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notes explaining how the issue was resolved",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the issue was resolved",
    )

    # Soft Delete Support (data-architecture.md Section 4)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp of soft deletion (null for active records)",
    )

    # Scoped Manager by default
    objects = IncidentManager()
    all_objects = models.Manager()

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        db_table = "incidents"
        indexes = [
            # Composite tenant indexes specified in data-architecture.md
            models.Index(fields=["campus", "status", "-created_at"], name="idx_incidents_tenant_status"),
            models.Index(fields=["campus", "category", "priority"], name="idx_incidents_tenant_cat_prio"),
            models.Index(fields=["campus", "reporter"], name="idx_incidents_tenant_reporter"),
            models.Index(fields=["campus", "building"], name="idx_incidents_tenant_building"),
            models.Index(fields=["campus", "department"], name="idx_incidents_tenant_dept"),
        ]
        constraints = [
            # Prevent incident from marking itself as a duplicate
            models.CheckConstraint(
                condition=~models.Q(is_duplicate_of=models.F("id")),
                name="check_incident_not_self_duplicate",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        campus_code = self.campus.code if self.campus else "NO-CAMPUS"
        return f"[{self.priority}] {self.title} ({self.status}) [{campus_code}]"

    def clean(self):
        super().clean()

        # 1. Tenant boundary validation
        if not self.campus_id:
            raise ValidationError({"campus": "Incident must belong to a Campus."})

        if self.campus and self.organization_id and self.campus.organization_id != self.organization_id:
            raise ValidationError({"campus": "Campus must belong to the same Organization."})

        if self.reporter_id and self.reporter.organization_id != self.organization_id:
            raise ValidationError({"reporter": "Reporter must belong to the same Organization."})

        # 2. Location graph integrity and auto-derivation
        if self.asset_id:
            if self.asset.campus_id != self.campus_id:
                raise ValidationError({"asset": "Asset belongs to a different Campus."})
            # Derive or validate building from asset
            if self.asset.building_id:
                if not self.building_id:
                    self.building_id = self.asset.building_id
                elif self.building_id != self.asset.building_id:
                    raise ValidationError({"building": "Building does not match Asset's building."})
            # Derive or validate floor from asset
            if self.asset.floor_id:
                if not self.floor_id:
                    self.floor_id = self.asset.floor_id
                elif self.floor_id != self.asset.floor_id:
                    raise ValidationError({"floor": "Floor does not match Asset's floor."})
            # Derive or validate room from asset
            if self.asset.room_id:
                if not self.room_id:
                    self.room_id = self.asset.room_id
                elif self.room_id != self.asset.room_id:
                    raise ValidationError({"room": "Room does not match Asset's room."})

        if self.room_id:
            if self.room.campus_id != self.campus_id:
                raise ValidationError({"room": "Room belongs to a different Campus."})
            if not self.building_id:
                self.building_id = self.room.building_id
            elif self.building_id != self.room.building_id:
                raise ValidationError({"building": "Building does not match Room's building."})

            if not self.floor_id:
                self.floor_id = self.room.floor_id
            elif self.floor_id != self.room.floor_id:
                raise ValidationError({"floor": "Floor does not match Room's floor."})

        if self.floor_id:
            if self.floor.campus_id != self.campus_id:
                raise ValidationError({"floor": "Floor belongs to a different Campus."})
            if not self.building_id:
                self.building_id = self.floor.building_id
            elif self.building_id != self.floor.building_id:
                raise ValidationError({"building": "Building does not match Floor's building."})

        if self.building_id and self.building.campus_id != self.campus_id:
            raise ValidationError({"building": "Building belongs to a different Campus."})

        # 3. Department boundary validation
        if self.department_id and self.department.campus_id != self.campus_id:
            raise ValidationError({"department": "Department belongs to a different Campus."})

        # 4. Duplicate relationship validation
        if self.is_duplicate_of_id:
            if self.is_duplicate_of_id == self.id:
                raise ValidationError({"is_duplicate_of": "An incident cannot be a duplicate of itself."})
            if self.is_duplicate_of.campus_id != self.campus_id:
                raise ValidationError({"is_duplicate_of": "Master incident belongs to a different Campus."})

        # 5. Lifecycle state transition validation on existing instances
        if self.pk:
            try:
                original = Incident.all_objects.get(pk=self.pk)
                if original.status != self.status:
                    allowed = VALID_TRANSITIONS.get(original.status, set())
                    if self.status not in allowed:
                        raise ValidationError({
                            "status": f"Invalid state transition from '{original.status}' to '{self.status}'."
                        })
            except Incident.DoesNotExist:
                pass

        # 6. Resolution timestamp consistency
        if self.status in [IncidentStatus.RESOLVED, IncidentStatus.VERIFIED, IncidentStatus.CLOSED]:
            if not self.resolved_at:
                self.resolved_at = timezone.now()
        elif self.status in [IncidentStatus.INGESTED, IncidentStatus.TRIAGING, IncidentStatus.ASSIGNED, IncidentStatus.IN_PROGRESS, IncidentStatus.REOPENED]:
            # If reopened or resumed, clear resolved_at if transitioning back
            if self.resolved_at and self.status == IncidentStatus.REOPENED:
                self.resolved_at = None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Soft deletes the incident without purging historical operational data."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])


class IncidentEvent(TenantScopedModel):
    """
    Immutable chronological operational timeline event for an incident.
    Captures state transitions, priority changes, reassignments, and notes.
    Adheres to ADR-007 append-only relational audit guarantees.
    """
    campus_scoped = True

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="events",
        db_index=True,
        help_text="Parent incident",
    )
    event_type = models.CharField(
        max_length=50,
        choices=IncidentEventType.choices,
        db_index=True,
        help_text="Type of operational event",
    )
    description = models.TextField(
        help_text="Human-readable event summary or log entry",
    )
    actor = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incident_events",
        help_text="User who initiated this event (null for system/agent actions)",
    )
    actor_type = models.CharField(
        max_length=32,
        choices=ActorType.choices,
        default=ActorType.USER,
        db_index=True,
        help_text="Type of actor (USER, SYSTEM, AGENT)",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured event payload (e.g. from_status, to_status)",
    )
    request_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Client or HTTP request correlation ID",
    )

    objects = IncidentEventManager()
    all_objects = models.Manager()

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Incident Event"
        verbose_name_plural = "Incident Events"
        db_table = "incident_events"
        indexes = [
            models.Index(fields=["incident", "-created_at"], name="idx_incident_events_timeline"),
            models.Index(fields=["campus", "event_type"], name="idx_incident_events_type"),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"[{self.event_type}] Incident {self.incident_id}: {self.description[:50]}"

    def clean(self):
        super().clean()
        if not self.incident_id:
            raise ValidationError({"incident": "Incident event must reference an Incident."})
        # Automatically derive organization and campus from parent incident
        if self.incident:
            if not self.organization_id:
                self.organization_id = self.incident.organization_id
            elif self.organization_id != self.incident.organization_id:
                raise ValidationError({"organization": "Organization must match parent Incident."})

            if not self.campus_id:
                self.campus_id = self.incident.campus_id
            elif self.campus_id != self.incident.campus_id:
                raise ValidationError({"campus": "Campus must match parent Incident."})

    def save(self, *args, **kwargs):
        # Enforce append-only immutability
        if not self._state.adding and self.pk:
            raise IncidentEventImmutableError("Incident event records are immutable and cannot be updated.")
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise IncidentEventImmutableError("Incident event records are immutable and cannot be deleted.")
