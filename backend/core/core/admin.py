"""
Django Admin registration for Paraxis AI Core Platform.
Enforces read-only protection for immutable AuditLog entries.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.models.organization import Organization, Campus
from core.models.access import Permission, Role
from core.models.user import User
from core.models.audit import AuditLog
from core.models.campus_graph import (
    Department,
    Building,
    Floor,
    Room,
    Asset,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    ordering = ("name",)


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "organization", "status", "timezone")
    list_filter = ("status", "organization")
    search_fields = ("name", "code", "organization__name")
    ordering = ("organization", "name")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "module")
    list_filter = ("module",)
    search_fields = ("codename", "name")
    ordering = ("module", "codename")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_system_role", "organization", "created_at")
    list_filter = ("is_system_role", "organization")
    search_fields = ("name", "description")
    filter_horizontal = ("permissions",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "organization", "primary_campus", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser", "organization")
    search_fields = ("email", "full_name")
    ordering = ("email",)
    filter_horizontal = ("roles", "groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone_number")}),
        ("Tenant Affiliation", {"fields": ("organization", "primary_campus")}),
        ("Roles & Permissions", {"fields": ("roles", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Read-only Django admin interface for immutable audit trails.
    Disallows adding, changing, or deleting audit records.
    """
    list_display = ("action", "entity_type", "entity_id", "actor", "actor_type", "organization", "campus", "created_at")
    list_filter = ("action", "actor_type", "entity_type", "organization")
    search_fields = ("action", "entity_type", "entity_id", "actor__email")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "campus", "organization", "status")
    list_filter = ("status", "campus", "organization")
    search_fields = ("name", "code")


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "campus", "floors_count", "status")
    list_filter = ("status", "campus", "organization")
    search_fields = ("name", "code")


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ("label", "floor_number", "building", "campus")
    list_filter = ("building__campus", "building")
    search_fields = ("label", "building__name")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "name", "room_type", "floor", "building", "status", "capacity")
    list_filter = ("room_type", "status", "building__campus", "building")
    search_fields = ("room_number", "name")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "asset_tag", "category", "department", "building", "room", "status")
    list_filter = ("category", "status", "department", "campus")
    search_fields = ("name", "asset_tag", "serial_number")
