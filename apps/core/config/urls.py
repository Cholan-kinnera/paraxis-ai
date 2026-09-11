"""
URL configuration for Paraxis AI Core Platform.
"""
from django.contrib import admin
from django.urls import path
from core.views.health import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    # Core platform health probe
    path("api/v1/health/", health_check, name="health_check"),
]
