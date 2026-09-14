"""
Serializers package for Paraxis AI Core Platform.
"""
from core.serializers.auth import (
    TokenObtainSerializer,
    TokenRefreshSerializer,
    UserProfileSerializer,
)
from core.serializers.organization import (
    OrganizationSerializer,
    CampusSerializer,
)
from core.serializers.access import (
    RoleSerializer,
    PermissionSerializer,
)

from core.serializers.campus_graph import (
    DepartmentSerializer,
    BuildingSerializer,
    FloorSerializer,
    RoomSerializer,
    AssetSerializer,
)

__all__ = [
    "TokenObtainSerializer",
    "TokenRefreshSerializer",
    "UserProfileSerializer",
    "OrganizationSerializer",
    "CampusSerializer",
    "RoleSerializer",
    "PermissionSerializer",
    "DepartmentSerializer",
    "BuildingSerializer",
    "FloorSerializer",
    "RoomSerializer",
    "AssetSerializer",
]
