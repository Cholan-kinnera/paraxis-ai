"""
URL configuration for Paraxis AI Core Platform.
Exposes canonical Phase 1 APIs and health probe.
"""
from django.contrib import admin
from django.urls import path
from core.views.health import health_check
from core.views.auth import TokenObtainView, TokenRefreshView, UserProfileView
from core.views.organization import OrganizationListCreateView, OrganizationDetailView
from core.views.campus import CampusListCreateView, CampusDetailView
from core.views.access import RoleListView

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
]
