"""
Organization API views for Paraxis AI Core Platform.
Enforces strict multi-tenancy: users can only access their own organization.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from core.models.organization import Organization
from core.serializers.organization import OrganizationSerializer
from core.permissions.rbac import IsAuthenticatedUser, IsSuperAdmin
from core.services.audit import log_audit_event


class OrganizationListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/organizations/ (List organizations accessible to caller)
    POST /api/v1/organizations/ (Provision new organization - Super Admin only)
    """
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSuperAdmin()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.has_role("SUPER_ADMIN"):
            return Organization.objects.all()
        if user.organization_id:
            return Organization.objects.filter(id=user.organization_id)
        return Organization.objects.none()

    def perform_create(self, serializer):
        org = serializer.save()
        log_audit_event(
            action="organization.create",
            entity_type="Organization",
            entity_id=str(org.id),
            actor=self.request.user,
            organization=org,
            request=self.request,
            post_state=serializer.data,
        )


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/organizations/<id>/
    PATCH /api/v1/organizations/<id>/
    """
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [IsSuperAdmin()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.has_role("SUPER_ADMIN"):
            return Organization.objects.all()
        if user.organization_id:
            return Organization.objects.filter(id=user.organization_id)
        return Organization.objects.none()

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = OrganizationSerializer(instance).data
        updated_org = serializer.save()
        log_audit_event(
            action="organization.update",
            entity_type="Organization",
            entity_id=str(updated_org.id),
            actor=self.request.user,
            organization=updated_org,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )
