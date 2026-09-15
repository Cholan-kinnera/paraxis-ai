"""
DRF Serializers for Incident & Issue Management (Phase 3).
Enforces strict tenant isolation, location graph derivation & validation,
lifecycle transition checks, and immutable timeline representations.
"""
from rest_framework import serializers
from core.models.incident import (
    Incident,
    IncidentEvent,
    IncidentStatus,
    IncidentPriority,
    IncidentCategory,
    IncidentSource,
    IncidentEventType,
    VALID_TRANSITIONS,
)
from core.models.campus_graph import Department, Building, Floor, Room, Asset
from core.models.user import User


class IncidentEventSerializer(serializers.ModelSerializer):
    """
    Serializer for immutable chronological incident events (timeline).
    """
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)
    actor_email = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = IncidentEvent
        fields = [
            "id",
            "incident_id",
            "event_type",
            "description",
            "actor_id",
            "actor_name",
            "actor_email",
            "actor_type",
            "metadata",
            "request_id",
            "created_at",
        ]
        read_only_fields = fields


class IncidentSerializer(serializers.ModelSerializer):
    """
    Serializer for Incident creation, retrieval, and updates.
    Handles location derivation from Campus Operational Graph and validates state transitions.
    """
    organization_id = serializers.UUIDField(read_only=True)
    campus_id = serializers.UUIDField(read_only=True)
    reporter_id = serializers.UUIDField(read_only=True)
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)
    reporter_email = serializers.CharField(source="reporter.email", read_only=True)

    # Optional foreign key write-only / ID inputs
    department_id = serializers.UUIDField(required=False, allow_null=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    assigned_to_id = serializers.UUIDField(required=False, allow_null=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    building_id = serializers.UUIDField(required=False, allow_null=True)
    building_name = serializers.CharField(source="building.name", read_only=True)
    building_code = serializers.CharField(source="building.code", read_only=True)

    floor_id = serializers.UUIDField(required=False, allow_null=True)
    floor_label = serializers.CharField(source="floor.label", read_only=True)
    floor_number = serializers.IntegerField(source="floor.floor_number", read_only=True)

    room_id = serializers.UUIDField(required=False, allow_null=True)
    room_number = serializers.CharField(source="room.room_number", read_only=True)

    asset_id = serializers.UUIDField(required=False, allow_null=True)
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)

    is_duplicate_of_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Incident
        fields = [
            "id",
            "organization_id",
            "campus_id",
            "reporter_id",
            "reporter_name",
            "reporter_email",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "source",
            "department_id",
            "department_name",
            "assigned_to_id",
            "assigned_to_name",
            "building_id",
            "building_name",
            "building_code",
            "floor_id",
            "floor_label",
            "floor_number",
            "room_id",
            "room_number",
            "asset_id",
            "asset_tag",
            "asset_name",
            "is_duplicate_of_id",
            "resolution_notes",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_id",
            "campus_id",
            "reporter_id",
            "reporter_name",
            "reporter_email",
            "department_name",
            "assigned_to_name",
            "building_name",
            "building_code",
            "floor_label",
            "floor_number",
            "room_number",
            "asset_tag",
            "asset_name",
            "resolved_at",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Incident title cannot be empty.")
        return val

    def validate_description(self, value):
        val = value.strip()
        if not val:
            raise serializers.ValidationError("Incident description cannot be empty.")
        return val

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = getattr(self, "instance", None)

        # 1. Resolve tenant context
        org_id = getattr(request, "active_organization_id", None) or (user.organization_id if user else None)
        campus_id = getattr(request, "active_campus_id", None) or (user.primary_campus_id if user else None)

        if instance:
            org_id = instance.organization_id
            campus_id = instance.campus_id

        if not org_id:
            raise serializers.ValidationError({"organization_id": "Organization context is required."})
        if not campus_id:
            raise serializers.ValidationError({"campus_id": "Campus context is required."})

        attrs["organization_id"] = org_id
        attrs["campus_id"] = campus_id

        # 2. Set reporter on creation
        if not instance:
            attrs["reporter"] = user

        # 3. Location graph derivation and validation
        asset_id = attrs.get("asset_id", instance.asset_id if instance else None)
        room_id = attrs.get("room_id", instance.room_id if instance else None)
        floor_id = attrs.get("floor_id", instance.floor_id if instance else None)
        building_id = attrs.get("building_id", instance.building_id if instance else None)

        asset = None
        room = None
        floor = None
        building = None

        if asset_id:
            try:
                asset = Asset.all_objects.filter(campus_id=campus_id).get(id=asset_id)
            except Asset.DoesNotExist:
                raise serializers.ValidationError({"asset_id": "Asset not found within your campus."})
            attrs["asset"] = asset

            # Derive location from asset if not explicitly provided
            if not room_id and asset.room_id:
                room_id = asset.room_id
            if not floor_id and asset.floor_id:
                floor_id = asset.floor_id
            if not building_id and asset.building_id:
                building_id = asset.building_id

            # Validate consistency if both provided
            if room_id and asset.room_id and room_id != asset.room_id:
                raise serializers.ValidationError({"room_id": "Specified room does not match asset's room location."})
            if building_id and asset.building_id and building_id != asset.building_id:
                raise serializers.ValidationError({"building_id": "Specified building does not match asset's building location."})

        if room_id:
            try:
                room = Room.all_objects.filter(campus_id=campus_id).get(id=room_id)
            except Room.DoesNotExist:
                raise serializers.ValidationError({"room_id": "Room not found within your campus."})
            attrs["room"] = room

            # Derive building and floor from room
            if not floor_id:
                floor_id = room.floor_id
            elif floor_id != room.floor_id:
                raise serializers.ValidationError({"floor_id": "Floor does not match room's floor."})

            if not building_id:
                building_id = room.building_id
            elif building_id != room.building_id:
                raise serializers.ValidationError({"building_id": "Building does not match room's building."})

        if floor_id:
            try:
                floor = Floor.all_objects.filter(campus_id=campus_id).get(id=floor_id)
            except Floor.DoesNotExist:
                raise serializers.ValidationError({"floor_id": "Floor not found within your campus."})
            attrs["floor"] = floor

            if not building_id:
                building_id = floor.building_id
            elif building_id != floor.building_id:
                raise serializers.ValidationError({"building_id": "Building does not match floor's building."})

        if building_id:
            try:
                building = Building.all_objects.filter(campus_id=campus_id).get(id=building_id)
            except Building.DoesNotExist:
                raise serializers.ValidationError({"building_id": "Building not found within your campus."})
            attrs["building"] = building

        # 4. Department validation
        dept_id = attrs.get("department_id", instance.department_id if instance else None)
        if dept_id:
            try:
                department = Department.all_objects.filter(campus_id=campus_id).get(id=dept_id)
                attrs["department"] = department
            except Department.DoesNotExist:
                raise serializers.ValidationError({"department_id": "Department not found within your campus."})

        # 5. Assigned user validation
        assigned_user_id = attrs.get("assigned_to_id", instance.assigned_to_id if instance else None)
        if assigned_user_id:
            try:
                assigned_user = User.objects.filter(organization_id=org_id).get(id=assigned_user_id)
                attrs["assigned_to"] = assigned_user
            except User.DoesNotExist:
                raise serializers.ValidationError({"assigned_to_id": "Assigned user not found within your organization."})

        # 6. Duplicate relation validation
        dup_id = attrs.get("is_duplicate_of_id", instance.is_duplicate_of_id if instance else None)
        if dup_id:
            if instance and str(instance.id) == str(dup_id):
                raise serializers.ValidationError({"is_duplicate_of_id": "An incident cannot be a duplicate of itself."})
            try:
                master = Incident.all_objects.filter(campus_id=campus_id).get(id=dup_id)
                attrs["is_duplicate_of"] = master
            except Incident.DoesNotExist:
                raise serializers.ValidationError({"is_duplicate_of_id": "Master incident not found within your campus."})

        # 7. State transition validation on update
        if instance and "status" in attrs:
            new_status = attrs["status"]
            old_status = instance.status
            if new_status != old_status:
                allowed_transitions = VALID_TRANSITIONS.get(old_status, set())
                if new_status not in allowed_transitions:
                    raise serializers.ValidationError({
                        "status": f"Invalid state transition from '{old_status}' to '{new_status}'."
                    })

                # RBAC constraints on status transition
                is_admin = (
                    user.is_superuser
                    or user.has_role("SUPER_ADMIN")
                    or user.has_role("CAMPUS_ADMIN")
                    or user.has_perm_code("incident:manage_all")
                    or user.has_perm_code("incident:update")
                )
                if not is_admin:
                    if old_status == IncidentStatus.RESOLVED and new_status in [IncidentStatus.VERIFIED, IncidentStatus.REOPENED]:
                        pass
                    else:
                        raise serializers.ValidationError({
                            "status": f"You do not have permission to transition incidents to '{new_status}'."
                        })

        # 8. RBAC constraints on administrative fields on update
        if instance:
            is_admin = (
                user.is_superuser
                or user.has_role("SUPER_ADMIN")
                or user.has_role("CAMPUS_ADMIN")
                or user.has_perm_code("incident:manage_all")
                or user.has_perm_code("incident:update")
            )
            if not is_admin:
                for admin_field in ["assigned_to_id", "department_id", "priority"]:
                    if admin_field in attrs:
                        raise serializers.ValidationError({
                            admin_field: f"You do not have permission to modify '{admin_field}'."
                        })
        if not instance:
            # Creation: non-admin students cannot set administrative fields directly
            is_admin = (
                user.is_superuser
                or user.has_role("SUPER_ADMIN")
                or user.has_role("CAMPUS_ADMIN")
                or user.has_perm_code("incident:manage_all")
            )
            if not is_admin and user and user.has_role("STUDENT"):
                if attrs.get("priority") and attrs["priority"] in [IncidentPriority.HIGH, IncidentPriority.CRITICAL]:
                    if not user.has_perm_code("incident:create_priority"):
                        attrs["priority"] = IncidentPriority.MEDIUM
                # Default status for new student reports is INGESTED
                attrs["status"] = IncidentStatus.INGESTED

        return attrs
