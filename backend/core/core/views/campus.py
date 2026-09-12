"""
Campus API views for Paraxis AI Core Platform.
Guarantees tenant isolation: campus queries are always scoped to the caller's organization.
"""
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, NotFound
from core.models.organization import Campus
from core.serializers.organization import CampusSerializer
from core.permissions.rbac import IsAuthenticatedUser, IsCampusAdmin
from core.services.audit import log_audit_event


class CampusListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/campuses/ (List campuses belonging to caller's organization)
    POST /api/v1/campuses/ (Create a new campus - Campus Admin / Super Admin)
    """
    serializer_class = CampusSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsCampusAdmin()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Campus.objects.all().select_related("organization")
        if user.organization_id:
            return Campus.objects.filter(organization_id=user.organization_id).select_related("organization")
        return Campus.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        org_id = serializer.validated_data.get("organization_id")
        if not org_id:
            org_id = user.organization_id
            serializer.validated_data["organization_id"] = org_id

        campus = serializer.save()
        log_audit_event(
            action="campus.create",
            entity_type="Campus",
            entity_id=str(campus.id),
            actor=user,
            organization=campus.organization,
            campus=campus,
            request=self.request,
            post_state=serializer.data,
        )


class CampusDetailView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/campuses/<id>/
    PATCH /api/v1/campuses/<id>/
    Fails closed (404) if the requested campus belongs to another organization.
    """
    serializer_class = CampusSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [IsCampusAdmin()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Campus.objects.all().select_related("organization")
        if user.organization_id:
            return Campus.objects.filter(organization_id=user.organization_id).select_related("organization")
        return Campus.objects.none()

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = CampusSerializer(instance).data
        updated_campus = serializer.save()
        log_audit_event(
            action="campus.update",
            entity_type="Campus",
            entity_id=str(updated_campus.id),
            actor=self.request.user,
            organization=updated_campus.organization,
            campus=updated_campus,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )
