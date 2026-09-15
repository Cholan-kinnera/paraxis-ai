"""
API views for Incident & Issue Management (Phase 3).
Guarantees tenant isolation, granular RBAC, timeline event capture, and immutable audit logging.
"""
from django.db import transaction
from django.http import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from core.models.incident import (
    Incident,
    IncidentEvent,
    IncidentStatus,
    IncidentEventType,
)
from core.models.audit import ActorType
from core.serializers.incident import (
    IncidentSerializer,
    IncidentEventSerializer,
)
from core.permissions.rbac import (
    IsAuthenticatedUser,
    IsCampusAdmin,
)
from core.services.audit import log_audit_event


def get_scoped_incident_queryset(request, select_related=True):
    """
    Returns an Incident queryset strictly scoped to the caller's tenant.
    Filters out soft-deleted records.
    Fails closed if the caller lacks organization context.
    """
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        return Incident.all_objects.none()

    if user.is_superuser:
        qs = Incident.all_objects.filter(deleted_at__isnull=True)
    elif user.organization_id:
        qs = Incident.all_objects.filter(
            organization_id=user.organization_id,
            deleted_at__isnull=True,
        )
        campus_id = getattr(request, "active_campus_id", None) or user.primary_campus_id
        if campus_id:
            qs = qs.filter(campus_id=campus_id)
        else:
            return Incident.all_objects.none()
    else:
        return Incident.all_objects.none()

    # RBAC Scoping: If caller lacks full view (e.g., student or non-admin staff without read capability)
    has_full_view = (
        user.is_superuser
        or user.has_role("SUPER_ADMIN")
        or user.has_role("CAMPUS_ADMIN")
        or user.has_perm_code("incident:manage_all")
        or user.has_perm_code("incident:read")
    )
    if not has_full_view:
        qs = qs.filter(reporter_id=user.id)

    if select_related:
        qs = qs.select_related(
            "reporter",
            "department",
            "assigned_to",
            "building",
            "floor",
            "room",
            "asset",
        )
    return qs


class IncidentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/incidents/ (List incidents in caller's campus)
    POST /api/v1/incidents/ (Submit a new incident report)
    """
    serializer_class = IncidentSerializer

    def get_permissions(self):
        return [IsAuthenticatedUser()]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.method == "POST":
            user = request.user
            is_authorized = (
                user.is_superuser
                or user.has_role("SUPER_ADMIN")
                or user.has_role("CAMPUS_ADMIN")
                or user.has_perm_code("incident:create")
                or user.has_perm_code("incident:manage_all")
            )
            if not is_authorized:
                raise PermissionDenied("You do not have permission to report incidents.")

    def get_queryset(self):
        qs = get_scoped_incident_queryset(self.request)

        # Query param filters
        params = self.request.query_params
        status_param = params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        priority_param = params.get("priority")
        if priority_param:
            qs = qs.filter(priority=priority_param)

        category_param = params.get("category")
        if category_param:
            qs = qs.filter(category=category_param)

        building_param = params.get("building")
        if building_param:
            qs = qs.filter(building_id=building_param)

        floor_param = params.get("floor")
        if floor_param:
            qs = qs.filter(floor_id=floor_param)

        room_param = params.get("room")
        if room_param:
            qs = qs.filter(room_id=room_param)

        asset_param = params.get("asset")
        if asset_param:
            qs = qs.filter(asset_id=asset_param)

        department_param = params.get("department")
        if department_param:
            qs = qs.filter(department_id=department_param)

        reporter_param = params.get("reporter")
        if reporter_param and (
            self.request.user.is_superuser
            or self.request.user.has_role("CAMPUS_ADMIN")
            or self.request.user.has_perm_code("incident:manage_all")
        ):
            qs = qs.filter(reporter_id=reporter_param)

        return qs

    def perform_create(self, serializer):
        request = self.request
        user = request.user
        req_id = getattr(request, "correlation_id", "") or request.headers.get("X-Request-ID", "")

        with transaction.atomic():
            incident = serializer.save()

            # Record initial timeline event
            IncidentEvent.objects.create(
                organization=incident.organization,
                campus=incident.campus,
                incident=incident,
                event_type=IncidentEventType.REPORTED,
                description=f"Incident '{incident.title}' reported by {user.full_name or user.email}.",
                actor=user,
                actor_type=ActorType.USER,
                request_id=req_id,
                metadata={
                    "category": incident.category,
                    "priority": incident.priority,
                    "status": incident.status,
                    "source": incident.source,
                },
            )

            # Record immutable audit log
            log_audit_event(
                action="incident.create",
                entity_type="Incident",
                entity_id=str(incident.id),
                actor=user,
                organization=incident.organization,
                campus=incident.campus,
                request=request,
                post_state=serializer.data,
            )


class IncidentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/incidents/<id>/
    PATCH /api/v1/incidents/<id>/
    DELETE /api/v1/incidents/<id>/
    """
    serializer_class = IncidentSerializer

    def get_permissions(self):
        return [IsAuthenticatedUser()]

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.method == "DELETE":
            user = request.user
            is_authorized = (
                user.is_superuser
                or user.has_role("SUPER_ADMIN")
                or user.has_role("CAMPUS_ADMIN")
                or user.has_perm_code("incident:delete")
                or user.has_perm_code("incident:manage_all")
            )
            if not is_authorized:
                raise PermissionDenied("You do not have permission to delete incidents.")

    def get_queryset(self):
        return get_scoped_incident_queryset(self.request)

    def perform_update(self, serializer):
        request = self.request
        user = request.user
        instance = self.get_object()
        req_id = getattr(request, "correlation_id", "") or request.headers.get("X-Request-ID", "")

        pre_state = IncidentSerializer(instance).data
        old_status = instance.status
        old_priority = instance.priority
        old_department_id = instance.department_id
        old_assigned_to_id = instance.assigned_to_id

        with transaction.atomic():
            incident = serializer.save()
            post_state = serializer.data

            # Timeline event 1: Status change
            if incident.status != old_status:
                event_type = IncidentEventType.STATUS_CHANGED
                if incident.status == IncidentStatus.RESOLVED:
                    event_type = IncidentEventType.RESOLVED
                elif incident.status == IncidentStatus.VERIFIED:
                    event_type = IncidentEventType.VERIFIED
                elif incident.status == IncidentStatus.REOPENED:
                    event_type = IncidentEventType.REOPENED
                elif incident.status == IncidentStatus.CLOSED:
                    event_type = IncidentEventType.CLOSED

                IncidentEvent.objects.create(
                    organization=incident.organization,
                    campus=incident.campus,
                    incident=incident,
                    event_type=event_type,
                    description=f"Status changed from {old_status} to {incident.status}.",
                    actor=user,
                    actor_type=ActorType.USER,
                    request_id=req_id,
                    metadata={
                        "from_status": old_status,
                        "to_status": incident.status,
                        "resolution_notes": incident.resolution_notes,
                    },
                )

            # Timeline event 2: Priority change
            if incident.priority != old_priority:
                IncidentEvent.objects.create(
                    organization=incident.organization,
                    campus=incident.campus,
                    incident=incident,
                    event_type=IncidentEventType.PRIORITY_CHANGED,
                    description=f"Priority changed from {old_priority} to {incident.priority}.",
                    actor=user,
                    actor_type=ActorType.USER,
                    request_id=req_id,
                    metadata={
                        "from_priority": old_priority,
                        "to_priority": incident.priority,
                    },
                )

            # Timeline event 3: Assignment change
            if (
                incident.department_id != old_department_id
                or incident.assigned_to_id != old_assigned_to_id
            ):
                dept_name = incident.department.name if incident.department else "Unassigned"
                staff_name = incident.assigned_to.full_name if incident.assigned_to else "Unassigned"
                IncidentEvent.objects.create(
                    organization=incident.organization,
                    campus=incident.campus,
                    incident=incident,
                    event_type=IncidentEventType.ASSIGNMENT_CHANGED,
                    description=f"Assignment updated: Department: {dept_name}, Staff: {staff_name}.",
                    actor=user,
                    actor_type=ActorType.USER,
                    request_id=req_id,
                    metadata={
                        "department_id": str(incident.department_id) if incident.department_id else None,
                        "assigned_to_id": str(incident.assigned_to_id) if incident.assigned_to_id else None,
                    },
                )

            # Record immutable audit log
            log_audit_event(
                action="incident.update",
                entity_type="Incident",
                entity_id=str(incident.id),
                actor=user,
                organization=incident.organization,
                campus=incident.campus,
                request=request,
                pre_state=pre_state,
                post_state=post_state,
            )

    def perform_destroy(self, instance):
        request = self.request
        user = request.user
        pre_state = IncidentSerializer(instance).data
        incident_id = str(instance.id)
        org = instance.organization
        campus = instance.campus

        with transaction.atomic():
            instance.soft_delete()
            log_audit_event(
                action="incident.delete",
                entity_type="Incident",
                entity_id=incident_id,
                actor=user,
                organization=org,
                campus=campus,
                request=request,
                pre_state=pre_state,
            )


class IncidentEventsTimelineView(generics.ListAPIView):
    """
    GET /api/v1/incidents/<id>/events/
    Returns the chronological operational timeline events for a given incident.
    Fails closed with 404 if the incident does not exist in the caller's tenant.
    """
    serializer_class = IncidentEventSerializer

    def get_permissions(self):
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        incident_id = self.kwargs.get("id") or self.kwargs.get("pk")
        scoped_incidents = get_scoped_incident_queryset(self.request, select_related=False)

        try:
            incident = scoped_incidents.get(id=incident_id)
        except Incident.DoesNotExist:
            raise Http404("Incident not found.")

        return IncidentEvent.objects.filter(incident=incident).select_related("actor").order_by("created_at")
