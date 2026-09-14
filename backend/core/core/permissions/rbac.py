"""
Role-Based Access Control (RBAC) permission primitives for Paraxis AI.
Complies with docs/security/authorization-model.md.
"""
from typing import List, Union
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsAuthenticatedUser(BasePermission):
    """
    Allows access only to authenticated and active users.
    """

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )


class IsSuperAdmin(BasePermission):
    """
    Allows access only to global platform super administrators.
    """

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        return request.user.is_superuser or request.user.has_role("SUPER_ADMIN")


class IsCampusAdmin(BasePermission):
    """
    Allows access to Campus Administrators and Super Administrators.
    """

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        return (
            request.user.is_superuser
            or request.user.has_role("SUPER_ADMIN")
            or request.user.has_role("CAMPUS_ADMIN")
        )


def require_roles(*role_names: str):
    """
    Dynamic permission class factory requiring the caller to hold at least one of the given roles.
    """
    class RolePermission(BasePermission):
        def has_permission(self, request, view) -> bool:
            if not (request.user and request.user.is_authenticated and request.user.is_active):
                return False
            if request.user.is_superuser:
                return True
            return any(request.user.has_role(r) for r in role_names)

    RolePermission.__name__ = f"RequireRoles_{'_'.join(role_names)}"
    return RolePermission


def require_permission(permission_codename: str):
    """
    Dynamic permission class factory requiring the caller to hold a specific capability codename.
    """
    class GranularPermission(BasePermission):
        def has_permission(self, request, view) -> bool:
            if not (request.user and request.user.is_authenticated and request.user.is_active):
                return False
            if request.user.is_superuser:
                return True
            return request.user.has_perm_code(permission_codename)

    GranularPermission.__name__ = f"RequirePermission_{permission_codename.replace(':', '_')}"
    return GranularPermission


def require_entity_permission(entity: str, action: str):
    """
    Dynamic permission class factory for campus graph entities.
    Allows access if caller is Super Admin, Campus Admin, or holds the specific '{entity}:{action}' permission.
    """
    class EntityPermission(BasePermission):
        def has_permission(self, request, view) -> bool:
            if not (request.user and request.user.is_authenticated and request.user.is_active):
                return False
            if request.user.is_superuser or request.user.has_role("SUPER_ADMIN") or request.user.has_role("CAMPUS_ADMIN"):
                return True
            return request.user.has_perm_code(f"{entity}:{action}")

    EntityPermission.__name__ = f"RequireEntityPermission_{entity}_{action}"
    return EntityPermission
