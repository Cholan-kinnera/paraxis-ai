"""
API views for Campus Operational Graph:
Department, Building, Floor, Room, Asset.
Guarantees strict tenant isolation and audit logging.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from core.models.campus_graph import (
    Department,
    Building,
    Floor,
    Room,
    Asset,
)
from core.serializers.campus_graph import (
    DepartmentSerializer,
    BuildingSerializer,
    FloorSerializer,
    RoomSerializer,
    AssetSerializer,
)
from core.permissions.rbac import (
    IsAuthenticatedUser,
    IsCampusAdmin,
    require_entity_permission,
)
from core.services.audit import log_audit_event


def get_scoped_queryset(model_class, request, select_related_fields=None):
    """
    Helper returning queryset strictly scoped to authenticated caller's tenant.
    Fails closed if caller lacks organization context.
    """
    user = request.user
    if user.is_superuser:
        qs = model_class.all_objects.all()
    elif user.organization_id:
        qs = model_class.all_objects.filter(organization_id=user.organization_id)
        campus_id = getattr(request, "active_campus_id", None) or user.primary_campus_id
        if campus_id:
            qs = qs.filter(campus_id=campus_id)
    else:
        return model_class.all_objects.none()

    if select_related_fields:
        qs = qs.select_related(*select_related_fields)
    return qs


# ============================================================================
# DEPARTMENT VIEWS
# ============================================================================

class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/departments/ (List departments in caller's campus)
    POST /api/v1/departments/ (Create a department - Campus Admin)
    """
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_entity_permission("department", "create")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Department, self.request, ["escalation_contact"])

    def perform_create(self, serializer):
        dept = serializer.save()
        log_audit_event(
            action="department.create",
            entity_type="Department",
            entity_id=str(dept.id),
            actor=self.request.user,
            organization=dept.organization,
            campus=dept.campus,
            request=self.request,
            post_state=serializer.data,
        )


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/departments/<id>/
    PATCH /api/v1/departments/<id>/
    DELETE /api/v1/departments/<id>/
    """
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [require_entity_permission("department", "update")()]
        if self.request.method == "DELETE":
            return [require_entity_permission("department", "delete")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Department, self.request, ["escalation_contact"])

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = DepartmentSerializer(instance).data
        dept = serializer.save()
        log_audit_event(
            action="department.update",
            entity_type="Department",
            entity_id=str(dept.id),
            actor=self.request.user,
            organization=dept.organization,
            campus=dept.campus,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )

    def perform_destroy(self, instance):
        pre_state = DepartmentSerializer(instance).data
        dept_id = str(instance.id)
        org = instance.organization
        campus = instance.campus
        instance.delete()
        log_audit_event(
            action="department.delete",
            entity_type="Department",
            entity_id=dept_id,
            actor=self.request.user,
            organization=org,
            campus=campus,
            request=self.request,
            pre_state=pre_state,
        )


# ============================================================================
# BUILDING VIEWS
# ============================================================================

class BuildingListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/buildings/ (List buildings in caller's campus)
    POST /api/v1/buildings/ (Create a building - Campus Admin)
    """
    serializer_class = BuildingSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_entity_permission("building", "create")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Building, self.request)

    def perform_create(self, serializer):
        bldg = serializer.save()
        log_audit_event(
            action="building.create",
            entity_type="Building",
            entity_id=str(bldg.id),
            actor=self.request.user,
            organization=bldg.organization,
            campus=bldg.campus,
            request=self.request,
            post_state=serializer.data,
        )


class BuildingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/buildings/<id>/
    PATCH /api/v1/buildings/<id>/
    DELETE /api/v1/buildings/<id>/
    """
    serializer_class = BuildingSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [require_entity_permission("building", "update")()]
        if self.request.method == "DELETE":
            return [require_entity_permission("building", "delete")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Building, self.request)

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = BuildingSerializer(instance).data
        bldg = serializer.save()
        log_audit_event(
            action="building.update",
            entity_type="Building",
            entity_id=str(bldg.id),
            actor=self.request.user,
            organization=bldg.organization,
            campus=bldg.campus,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )

    def perform_destroy(self, instance):
        pre_state = BuildingSerializer(instance).data
        bldg_id = str(instance.id)
        org = instance.organization
        campus = instance.campus
        instance.delete()
        log_audit_event(
            action="building.delete",
            entity_type="Building",
            entity_id=bldg_id,
            actor=self.request.user,
            organization=org,
            campus=campus,
            request=self.request,
            pre_state=pre_state,
        )


# ============================================================================
# FLOOR VIEWS
# ============================================================================

class FloorListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/floors/ (List floors, filterable by ?building=<id>)
    POST /api/v1/floors/ (Create a floor - Campus Admin)
    """
    serializer_class = FloorSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_entity_permission("floor", "create")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        qs = get_scoped_queryset(Floor, self.request, ["building"])
        building_id = self.request.query_params.get("building")
        if building_id:
            qs = qs.filter(building_id=building_id)
        return qs

    def perform_create(self, serializer):
        floor = serializer.save()
        log_audit_event(
            action="floor.create",
            entity_type="Floor",
            entity_id=str(floor.id),
            actor=self.request.user,
            organization=floor.organization,
            campus=floor.campus,
            request=self.request,
            post_state=serializer.data,
        )


class FloorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/floors/<id>/
    PATCH /api/v1/floors/<id>/
    DELETE /api/v1/floors/<id>/
    """
    serializer_class = FloorSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [require_entity_permission("floor", "update")()]
        if self.request.method == "DELETE":
            return [require_entity_permission("floor", "delete")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Floor, self.request, ["building"])

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = FloorSerializer(instance).data
        floor = serializer.save()
        log_audit_event(
            action="floor.update",
            entity_type="Floor",
            entity_id=str(floor.id),
            actor=self.request.user,
            organization=floor.organization,
            campus=floor.campus,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )

    def perform_destroy(self, instance):
        pre_state = FloorSerializer(instance).data
        floor_id = str(instance.id)
        org = instance.organization
        campus = instance.campus
        instance.delete()
        log_audit_event(
            action="floor.delete",
            entity_type="Floor",
            entity_id=floor_id,
            actor=self.request.user,
            organization=org,
            campus=campus,
            request=self.request,
            pre_state=pre_state,
        )


# ============================================================================
# ROOM VIEWS
# ============================================================================

class RoomListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/rooms/ (List rooms, filterable by ?building=<id>&floor=<id>&room_type=<type>)
    POST /api/v1/rooms/ (Create a room - Campus Admin)
    """
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_entity_permission("room", "create")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        qs = get_scoped_queryset(Room, self.request, ["building", "floor"])
        building_id = self.request.query_params.get("building")
        if building_id:
            qs = qs.filter(building_id=building_id)
        floor_id = self.request.query_params.get("floor")
        if floor_id:
            qs = qs.filter(floor_id=floor_id)
        room_type = self.request.query_params.get("room_type")
        if room_type:
            qs = qs.filter(room_type=room_type)
        return qs

    def perform_create(self, serializer):
        room = serializer.save()
        log_audit_event(
            action="room.create",
            entity_type="Room",
            entity_id=str(room.id),
            actor=self.request.user,
            organization=room.organization,
            campus=room.campus,
            request=self.request,
            post_state=serializer.data,
        )


class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/rooms/<id>/
    PATCH /api/v1/rooms/<id>/
    DELETE /api/v1/rooms/<id>/
    """
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [require_entity_permission("room", "update")()]
        if self.request.method == "DELETE":
            return [require_entity_permission("room", "delete")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Room, self.request, ["building", "floor"])

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = RoomSerializer(instance).data
        room = serializer.save()
        log_audit_event(
            action="room.update",
            entity_type="Room",
            entity_id=str(room.id),
            actor=self.request.user,
            organization=room.organization,
            campus=room.campus,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )

    def perform_destroy(self, instance):
        pre_state = RoomSerializer(instance).data
        room_id = str(instance.id)
        org = instance.organization
        campus = instance.campus
        instance.delete()
        log_audit_event(
            action="room.delete",
            entity_type="Room",
            entity_id=room_id,
            actor=self.request.user,
            organization=org,
            campus=campus,
            request=self.request,
            pre_state=pre_state,
        )


# ============================================================================
# ASSET VIEWS
# ============================================================================

class AssetListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/assets/ (List assets, filterable by ?department=&building=&room=&category=&status=)
    POST /api/v1/assets/ (Create an asset - Campus Admin or Department Coordinator)
    """
    serializer_class = AssetSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_entity_permission("asset", "create")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        qs = get_scoped_queryset(Asset, self.request, ["department", "building", "floor", "room"])
        dept_id = self.request.query_params.get("department")
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        bldg_id = self.request.query_params.get("building")
        if bldg_id:
            qs = qs.filter(building_id=bldg_id)
        floor_id = self.request.query_params.get("floor")
        if floor_id:
            qs = qs.filter(floor_id=floor_id)
        room_id = self.request.query_params.get("room")
        if room_id:
            qs = qs.filter(room_id=room_id)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        asset = serializer.save()
        log_audit_event(
            action="asset.create",
            entity_type="Asset",
            entity_id=str(asset.id),
            actor=self.request.user,
            organization=asset.organization,
            campus=asset.campus,
            request=self.request,
            post_state=serializer.data,
        )


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/assets/<id>/
    PATCH /api/v1/assets/<id>/
    DELETE /api/v1/assets/<id>/
    """
    serializer_class = AssetSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [require_entity_permission("asset", "update")()]
        if self.request.method == "DELETE":
            return [require_entity_permission("asset", "delete")()]
        return [IsAuthenticatedUser()]

    def get_queryset(self):
        return get_scoped_queryset(Asset, self.request, ["department", "building", "floor", "room"])

    def perform_update(self, serializer):
        instance = self.get_object()
        pre_state = AssetSerializer(instance).data
        asset = serializer.save()
        log_audit_event(
            action="asset.update",
            entity_type="Asset",
            entity_id=str(asset.id),
            actor=self.request.user,
            organization=asset.organization,
            campus=asset.campus,
            request=self.request,
            pre_state=pre_state,
            post_state=serializer.data,
        )

    def perform_destroy(self, instance):
        pre_state = AssetSerializer(instance).data
        asset_id = str(instance.id)
        org = instance.organization
        campus = instance.campus
        instance.delete()
        log_audit_event(
            action="asset.delete",
            entity_type="Asset",
            entity_id=asset_id,
            actor=self.request.user,
            organization=org,
            campus=campus,
            request=self.request,
            pre_state=pre_state,
        )
