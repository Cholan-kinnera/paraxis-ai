"""
Custom User model and manager for Paraxis AI.
Implements institutional organization scoping, primary campus assignment, and RBAC bindings.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    """
    Manager for custom User model with normalized email lookup and superuser creation.
    """

    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must provide a valid email address.")
        if not full_name:
            raise ValueError("Users must provide a full name.")

        email = self.normalize_email(email).lower()
        user = self.model(email=email, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, full_name, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Core campus actor representing Students, Faculty, Staff, Wardens, Technicians, and Admins.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="User unique identifier (UUID v4)",
    )
    email = models.EmailField(
        max_length=255,
        db_index=True,
        help_text="Institutional or platform email address",
    )
    full_name = models.CharField(
        max_length=255,
        help_text="Legal or display full name",
    )
    phone_number = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Contact telephone number",
    )
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
        db_index=True,
        help_text="Institutional organization owning this user account",
    )
    primary_campus = models.ForeignKey(
        "core.Campus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        db_index=True,
        help_text="Primary campus of residence/operation for this user",
    )
    roles = models.ManyToManyField(
        "core.Role",
        related_name="users",
        blank=True,
        help_text="RBAC roles assigned to this user",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Designates whether this user account is active",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether user can access Django admin site",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Account creation timestamp",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last modification timestamp",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"
        ordering = ["-created_at"]
        constraints = [
            # Organization-scoped email uniqueness for institutional users
            models.UniqueConstraint(
                fields=["organization", "email"],
                condition=models.Q(organization__isnull=False),
                name="unique_organization_user_email",
            ),
            # Global email uniqueness for system superusers without organization
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(organization__isnull=True),
                name="unique_system_user_email",
            ),
        ]

    def __str__(self) -> str:
        org_slug = self.organization.slug if self.organization else "PLATFORM"
        return f"{self.email} ({org_slug})"

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()

        # Enforce cross-tenant invariant: User's campus must belong to the user's organization
        if self.primary_campus_id and self.organization_id:
            if self.primary_campus.organization_id != self.organization_id:
                raise ValidationError({
                    "primary_campus": "User primary campus must belong to the user's organization."
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def has_role(self, role_name: str) -> bool:
        if self.is_superuser:
            return True
        return self.roles.filter(name=role_name).exists()

    def has_perm_code(self, codename: str) -> bool:
        if self.is_superuser:
            return True
        return self.roles.filter(permissions__codename=codename).exists()

    def get_role_names(self) -> list[str]:
        return list(self.roles.values_list("name", flat=True))

    def get_permission_codenames(self) -> list[str]:
        if self.is_superuser:
            from core.models.access import Permission
            return list(Permission.objects.values_list("codename", flat=True))
        return list(self.roles.values_list("permissions__codename", flat=True).distinct())
