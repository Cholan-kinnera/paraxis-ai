"""
API views for SLA policy management.
"""
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from core.models.sla import SLA
from core.serializers.sla import SLASerializer
from core.permissions.rbac import IsAuthenticatedUser


class SLAListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/slas/ (List SLAs in caller's campus)
    POST /api/v1/slas/ (Define a new SLA policy)
    """
    serializer_class = SLASerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated or not user.is_active:
            return SLA.all_objects.none()

        if user.is_superuser:
            return SLA.all_objects.all()

        if not user.organization_id:
            return SLA.all_objects.none()

        campus_id = getattr(self.request, "active_campus_id", None) or user.primary_campus_id
        if not campus_id:
            return SLA.all_objects.none()

        return SLA.all_objects.filter(
            organization_id=user.organization_id,
            campus_id=campus_id,
        )

    def perform_create(self, serializer):
        user = self.request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("sla:manage")
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to define SLA policies.")

        campus_id = getattr(self.request, "active_campus_id", None) or user.primary_campus_id
        serializer.save(
            organization_id=user.organization_id,
            campus_id=campus_id,
        )
