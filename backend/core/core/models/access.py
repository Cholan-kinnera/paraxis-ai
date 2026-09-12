"""
Permission and Role models providing Role-Based Access Control (RBAC) for Paraxis AI.
"""
from django.core.exceptions import ValidationError
from django.db import models
from core.models.base import TimeStampedModel


class Permission(TimeStampedModel):
    """
    Granular capability string (e.g., 'incident:create', 'campus:manage').
    Codenames are unique and immutable across the platform.
    """
    codename = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Machine-readable capability identifier (e.g., 'incident:create')",
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable permission label",
    )
    module = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Functional module domain (e.g., 'incident', 'task', 'safety', 'auth')",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        db_table = "permissions"

    def __str__(self) -> str:
        return f"{self.codename} ({self.name})"


class Role(TimeStampedModel):
    """
    Named role for RBAC authorization.
    System roles (is_system_role=True) are global and protected against deletion/tampering.
    Organization roles are scoped to a specific institution.
    """
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="roles",
        db_index=True,
        help_text="Owning organization; null for platform-wide system roles",
    )
    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Role identifier name (e.g., 'STUDENT', 'CAMPUS_ADMIN')",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of role responsibilities and privileges",
    )
    is_system_role = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag indicating platform-protected immutable system role",
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
        help_text="Granular permissions granted to holders of this role",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        db_table = "roles"
        constraints = [
            # System roles have unique names globally
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(is_system_role=True),
                name="unique_system_role_name",
            ),
            # Organization-specific roles are unique per organization
            models.UniqueConstraint(
                fields=["organization", "name"],
                condition=models.Q(is_system_role=False),
                name="unique_organization_role_name",
            ),
        ]

    def __str__(self) -> str:
        scope = "SYSTEM" if self.is_system_role else (self.organization.slug if self.organization else "ORPHAN")
        return f"{self.name} [{scope}]"

    def clean(self):
        super().clean()
        if self.is_system_role and self.organization_id is not None:
            raise ValidationError({"organization": "System roles must not be bound to a specific organization."})

    def delete(self, *args, **kwargs):
        if self.is_system_role:
            raise ValidationError("Protected system roles cannot be deleted.")
        return super().delete(*args, **kwargs)
