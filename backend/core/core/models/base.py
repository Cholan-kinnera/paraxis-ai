"""
Base model definitions for Paraxis AI Core Platform.
Provides UUID primary keys, timestamp tracking, and multi-tenant scoping.
"""
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model providing UUID v4 primary keys and audit timestamps.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID v4)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the record was created",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last modified",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class TenantScopedQuerySet(models.QuerySet):
    """
    QuerySet providing explicit tenant-scoping methods.
    """

    def for_organization(self, organization_id):
        if hasattr(self.model, "organization_id"):
            return self.filter(organization_id=organization_id)
        return self

    def for_campus(self, campus_id):
        if hasattr(self.model, "campus_id"):
            return self.filter(campus_id=campus_id)
        return self


class TenantScopedManager(models.Manager.from_queryset(TenantScopedQuerySet)):
    """
    Manager that automatically enforces tenant boundaries using request context.
    Respects the difference between organization-scoped and campus-scoped data.
    Guarantees fail-closed isolation: returns an empty queryset if tenant context is missing.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        from core.context import get_current_campus_id, get_current_organization_id

        org_id = get_current_organization_id()
        campus_id = get_current_campus_id()

        # Invariant 1: Multi-tenant models require active organization context.
        # If organization context is missing, fail closed immediately.
        if not org_id:
            return qs.none()

        # Invariant 2: Check if model requires campus-level scoping.
        requires_campus_scope = getattr(self.model, "campus_scoped", False)
        if not requires_campus_scope and hasattr(self.model, "campus"):
            try:
                campus_field = self.model._meta.get_field("campus")
                if campus_field and not campus_field.null:
                    requires_campus_scope = True
            except Exception:
                pass

        # If campus context is strictly required but missing, fail closed.
        if requires_campus_scope and not campus_id:
            return qs.none()

        # Invariant 3: Apply verified tenant boundaries.
        filters = {}
        if hasattr(self.model, "organization"):
            filters["organization_id"] = org_id

        if campus_id and hasattr(self.model, "campus"):
            filters["campus_id"] = campus_id

        return qs.filter(**filters)


class TenantScopedModel(TimeStampedModel):
    """
    Abstract base model for all entities scoped to an Organization and optional Campus.
    Enforces automatic tenant filtering via TenantScopedManager.
    """
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        db_index=True,
        help_text="Owning organization for multi-tenancy",
    )
    campus = models.ForeignKey(
        "core.Campus",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_set",
        db_index=True,
        help_text="Owning campus if campus-scoped",
    )

    # Scoped manager by default
    objects = TenantScopedManager()
    # Explicit internal manager for migrations and system-level operations
    all_objects = models.Manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["organization", "campus"]),
        ]
