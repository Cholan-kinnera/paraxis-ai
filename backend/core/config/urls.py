"""
URL configuration for Paraxis AI Core Platform.
Exposes canonical Phase 1-4 APIs and health probe.
"""
from django.contrib import admin
from django.urls import path
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
from core.views.incident import (
    IncidentListCreateView,
    IncidentDetailView,
    IncidentEventsTimelineView,
)
from core.views.sla import (
    SLAListCreateView,
)
from core.views.task import (
    TaskListCreateView,
    TaskDetailView,
    TaskEventsTimelineView,
    TaskAssignView,
    TaskStartView,
    TaskCompleteView,
    TaskCancelView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Core platform health probe
    path("api/v1/health/", health_check, name="health_check"),

    # Authentication & Identity
    path("api/v1/auth/token/", TokenObtainView.as_view(), name="auth_token_obtain"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="auth_token_refresh"),
    path("api/v1/auth/me/", UserProfileView.as_view(), name="auth_user_profile"),

    # Organization Tenancy
    path("api/v1/organizations/", OrganizationListCreateView.as_view(), name="organization_list_create"),
    path("api/v1/organizations/<uuid:pk>/", OrganizationDetailView.as_view(), name="organization_detail"),

    # Campus Tenancy
    path("api/v1/campuses/", CampusListCreateView.as_view(), name="campus_list_create"),
    path("api/v1/campuses/<uuid:pk>/", CampusDetailView.as_view(), name="campus_detail"),

    # RBAC Roles
    path("api/v1/roles/", RoleListView.as_view(), name="role_list"),

    # Campus Operational Graph
    path("api/v1/departments/", DepartmentListCreateView.as_view(), name="department_list_create"),
    path("api/v1/departments/<uuid:pk>/", DepartmentDetailView.as_view(), name="department_detail"),

    path("api/v1/buildings/", BuildingListCreateView.as_view(), name="building_list_create"),
    path("api/v1/buildings/<uuid:pk>/", BuildingDetailView.as_view(), name="building_detail"),

    path("api/v1/floors/", FloorListCreateView.as_view(), name="floor_list_create"),
    path("api/v1/floors/<uuid:pk>/", FloorDetailView.as_view(), name="floor_detail"),

    path("api/v1/rooms/", RoomListCreateView.as_view(), name="room_list_create"),
    path("api/v1/rooms/<uuid:pk>/", RoomDetailView.as_view(), name="room_detail"),

    path("api/v1/assets/", AssetListCreateView.as_view(), name="asset_list_create"),
    path("api/v1/assets/<uuid:pk>/", AssetDetailView.as_view(), name="asset_detail"),

    # Incident & Issue Management (Phase 3)
    path("api/v1/incidents/", IncidentListCreateView.as_view(), name="incident_list_create"),
    path("api/v1/incidents/<uuid:pk>/", IncidentDetailView.as_view(), name="incident_detail"),
    path("api/v1/incidents/<uuid:pk>/events/", IncidentEventsTimelineView.as_view(), name="incident_events_timeline"),

    # SLA Management (Phase 4)
    path("api/v1/slas/", SLAListCreateView.as_view(), name="sla_list_create"),

    # Task & Dispatch Management (Phase 4)
    path("api/v1/tasks/", TaskListCreateView.as_view(), name="task_list_create"),
    path("api/v1/tasks/<uuid:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("api/v1/tasks/<uuid:pk>/events/", TaskEventsTimelineView.as_view(), name="task_events_timeline"),
    path("api/v1/tasks/<uuid:pk>/assign/", TaskAssignView.as_view(), name="task_assign"),
    path("api/v1/tasks/<uuid:pk>/start/", TaskStartView.as_view(), name="task_start"),
    path("api/v1/tasks/<uuid:pk>/complete/", TaskCompleteView.as_view(), name="task_complete"),
    path("api/v1/tasks/<uuid:pk>/cancel/", TaskCancelView.as_view(), name="task_cancel"),
]
