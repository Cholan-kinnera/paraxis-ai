"""
Role and Permission API views for Paraxis AI Core Platform.
"""
from django.db.models import Q
from rest_framework import generics
from core.models.access import Role
from core.serializers.access import RoleSerializer
from core.permissions.rbac import IsAuthenticatedUser


class RoleListView(generics.ListAPIView):
    """
    GET /api/v1/roles/
    List roles accessible to the caller (global system roles + caller's institutional roles).
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Role.objects.all().prefetch_related("permissions")
        if user.organization_id:
            return Role.objects.filter(
                Q(is_system_role=True) | Q(organization_id=user.organization_id)
            ).prefetch_related("permissions")
        return Role.objects.filter(is_system_role=True).prefetch_related("permissions")
