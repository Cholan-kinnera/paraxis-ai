"""
Organization and Campus models representing the institutional hierarchy for Paraxis AI.
"""
from django.core.exceptions import ValidationError
from django.db import models
from core.models.base import TimeStampedModel


class OrganizationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    TERMINATED = "TERMINATED", "Terminated"


class CampusStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    MAINTENANCE = "MAINTENANCE", "Maintenance"
    INACTIVE = "INACTIVE", "Inactive"


class Organization(TimeStampedModel):
    """
    Top-level institutional tenant entity (e.g., University System, Educational Trust).
    """
    name = models.CharField(max_length=255, help_text="Institutional name")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Globally unique institutional identifier slug",
    )
    status = models.CharField(
        max_length=32,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE,
        db_index=True,
        help_text="Lifecycle status of the organization",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        db_table = "organizations"

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class Campus(TimeStampedModel):
    """
    Physical or administrative campus branch belonging to an Organization.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="campuses",
        db_index=True,
        help_text="Parent organization owning this campus",
    )
    name = models.CharField(max_length=255, help_text="Campus name")
    code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Campus identifier code, unique within organization (e.g., 'ENG', 'MED')",
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="Local timezone identifier (e.g., 'Asia/Kolkata', 'UTC')",
    )
    address = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured physical address details",
    )
    status = models.CharField(
        max_length=32,
        choices=CampusStatus.choices,
        default=CampusStatus.ACTIVE,
        db_index=True,
        help_text="Operational status of this campus",
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"
        db_table = "campuses"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="unique_organization_campus_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.code}] ({self.organization.slug})"

    def clean(self):
        super().clean()
        if not self.organization_id:
            raise ValidationError({"organization": "Campus must belong to a valid Organization."})
