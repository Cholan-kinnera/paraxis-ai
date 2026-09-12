"""
Permissions package for Paraxis AI Core Platform.
"""
from core.permissions.rbac import (
    IsAuthenticatedUser,
    IsSuperAdmin,
    IsCampusAdmin,
    require_roles,
    require_permission,
)

__all__ = [
    "IsAuthenticatedUser",
    "IsSuperAdmin",
    "IsCampusAdmin",
    "require_roles",
    "require_permission",
]
