"""
Views package for Paraxis AI Core Platform.
"""
from core.views.health import health_check
from core.views.auth import TokenObtainView, TokenRefreshView, UserProfileView
from core.views.organization import OrganizationListCreateView, OrganizationDetailView
from core.views.campus import CampusListCreateView, CampusDetailView
from core.views.access import RoleListView

from core.views.campus_graph import (
    DepartmentListCreateView,
    DepartmentDetailView,
    BuildingListCreateView,
    BuildingDetailView,
    FloorListCreateView,
    FloorDetailView,
    RoomListCreateView,
    RoomDetailView,
    AssetListCreateView,
    AssetDetailView,
)

__all__ = [
    "health_check",
    "TokenObtainView",
    "TokenRefreshView",
    "UserProfileView",
    "OrganizationListCreateView",
    "OrganizationDetailView",
    "CampusListCreateView",
    "CampusDetailView",
    "RoleListView",
    "DepartmentListCreateView",
    "DepartmentDetailView",
    "BuildingListCreateView",
    "BuildingDetailView",
    "FloorListCreateView",
    "FloorDetailView",
    "RoomListCreateView",
    "RoomDetailView",
    "AssetListCreateView",
    "AssetDetailView",
]
