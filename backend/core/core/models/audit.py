"""
AuditLog model providing an immutable operational and security event trail.
Adheres to ADR-007: Append-only relational audit model with zero mutation allowance.
"""
import uuid
from django.core.exceptions import ValidationError
from django.db import models


class AuditLogImmutableError(ValidationError):
    """Raised when an attempt is made to modify or delete an immutable audit log."""
    pass


class ActorType(models.TextChoices):
    USER = "USER", "User"
    SYSTEM = "SYSTEM", "System"
    AGENT = "AGENT", "Agent"


class AuditLogQuerySet(models.QuerySet):
    """
    Immutable QuerySet preventing bulk update and delete operations.
    """

    def update(self, **kwargs):
        raise AuditLogImmutableError("Audit log entries are immutable and cannot be updated.")

    def delete(self):
        raise AuditLogImmutableError("Audit log entries are immutable and cannot be deleted.")


class AuditLogManager(models.Manager.from_queryset(AuditLogQuerySet)):
    pass


class AuditLog(models.Model):
    """
    Immutable append-only record of security-critical actions and entity mutations.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique audit record identifier (UUID v4)",
    )
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs",
        db_index=True,
        help_text="Institutional organization context for this event",
    )
    campus = models.ForeignKey(
        "core.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        db_index=True,
        help_text="Campus context for this event if applicable",
    )
    actor = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        db_index=True,
        help_text="User initiating the action (null for system/unauthenticated events)",
    )
    actor_type = models.CharField(
        max_length=32,
        choices=ActorType.choices,
        default=ActorType.USER,
        db_index=True,
        help_text="Type of actor (USER, SYSTEM, AGENT)",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Originating IP address of the caller",
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Action verb (e.g., 'auth.login', 'auth.failed', 'user.create', 'role.update')",
    )
    entity_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Target entity class name (e.g., 'User', 'Campus', 'Role')",
    )
    entity_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Target entity primary key identifier",
    )
    pre_state_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="State snapshot before the action occurred",
    )
    post_state_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="State snapshot after the action occurred",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when the action was recorded",
    )

    objects = AuditLogManager()

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "campus", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.action}] {self.entity_type}({self.entity_id}) by {self.actor_type}"

    def save(self, *args, **kwargs):
        # Enforce append-only immutability
        if not self._state.adding:
            raise AuditLogImmutableError("Audit log entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AuditLogImmutableError("Audit log entries are immutable and cannot be deleted.")
