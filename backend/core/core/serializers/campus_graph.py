"""
Serializers for Campus Operational Graph:
Department, Building, Floor, Room, Asset.
Enforces multi-tenant scoping and location hierarchy integrity.
"""
from rest_framework import serializers
from core.models.campus_graph import (
    Department,
    Building,
    Floor,
    Room,
    Asset,
    DepartmentStatus,
    BuildingStatus,
    RoomType,
    RoomStatus,
    AssetCategory,
    AssetStatus,
)
from core.models.user import User


class DepartmentSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(required=False)
    campus_id = serializers.UUIDField(required=False)
    escalation_contact_id = serializers.UUIDField(required=False, allow_null=True)
    escalation_contact_name = serializers.CharField(source="escalation_contact.full_name", read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "organization_id",
            "campus_id",
            "name",
            "code",
            "description",
            "contact_email",
            "escalation_contact_id",
            "escalation_contact_name",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = getattr(self, "instance", None)

        org_id = attrs.get("organization_id") or getattr(request, "active_organization_id", None) or (user.organization_id if user else None)
        campus_id = attrs.get("campus_id") or getattr(request, "active_campus_id", None) or (user.primary_campus_id if user else None)

        if instance:
            org_id = org_id or instance.organization_id
            campus_id = campus_id or instance.campus_id

        if not org_id:
            raise serializers.ValidationError({"organization_id": "Organization context is required."})
        if not campus_id:
            raise serializers.ValidationError({"campus_id": "Campus context is required."})

        attrs["organization_id"] = org_id
        attrs["campus_id"] = campus_id

        # Verify escalation contact
        escalation_contact_id = attrs.get("escalation_contact_id")
        if escalation_contact_id:
            try:
                contact = User.objects.get(id=escalation_contact_id, organization_id=org_id)
                attrs["escalation_contact"] = contact
            except User.DoesNotExist:
                raise serializers.ValidationError({"escalation_contact_id": "Escalation contact not found in this organization."})

        # Uniqueness check on code per campus
        code = attrs.get("code") or (instance.code if instance else None)
        if code and campus_id:
            qs = Department.all_objects.filter(campus_id=campus_id, code=code)
            if instance:
                qs = qs.exclude(id=instance.id)
            if qs.exists():
                raise serializers.ValidationError({"code": "A department with this code already exists on this campus."})

        return attrs


class BuildingSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(required=False)
    campus_id = serializers.UUIDField(required=False)

    class Meta:
        model = Building
        fields = [
            "id",
            "organization_id",
            "campus_id",
            "name",
            "code",
            "description",
            "floors_count",
            "status",
            "gis_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = getattr(self, "instance", None)

        org_id = attrs.get("organization_id") or getattr(request, "active_organization_id", None) or (user.organization_id if user else None)
        campus_id = attrs.get("campus_id") or getattr(request, "active_campus_id", None) or (user.primary_campus_id if user else None)

        if instance:
            org_id = org_id or instance.organization_id
            campus_id = campus_id or instance.campus_id

        if not org_id:
            raise serializers.ValidationError({"organization_id": "Organization context is required."})
        if not campus_id:
            raise serializers.ValidationError({"campus_id": "Campus context is required."})

        attrs["organization_id"] = org_id
        attrs["campus_id"] = campus_id

        # Unique code per campus
        code = attrs.get("code") or (instance.code if instance else None)
        if code and campus_id:
            qs = Building.all_objects.filter(campus_id=campus_id, code=code)
            if instance:
                qs = qs.exclude(id=instance.id)
            if qs.exists():
                raise serializers.ValidationError({"code": "A building with this code already exists on this campus."})

        return attrs


class FloorSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    campus_id = serializers.UUIDField(read_only=True)
    building_id = serializers.UUIDField(required=True)
    building_name = serializers.CharField(source="building.name", read_only=True)
    building_code = serializers.CharField(source="building.code", read_only=True)

    class Meta:
        model = Floor
        fields = [
            "id",
            "organization_id",
            "campus_id",
            "building_id",
            "building_name",
            "building_code",
            "floor_number",
            "label",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "campus_id", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = getattr(self, "instance", None)

        building_id = attrs.get("building_id") or (instance.building_id if instance else None)
        if not building_id:
            raise serializers.ValidationError({"building_id": "Building is required."})

        try:
            # Must scope building by user's organization if non-superuser
            bldg_qs = Building.all_objects.all()
            if user and not user.is_superuser:
                bldg_qs = bldg_qs.filter(organization_id=user.organization_id)
            building = bldg_qs.get(id=building_id)
        except Building.DoesNotExist:
            raise serializers.ValidationError({"building_id": "Building not found within your organization."})

        attrs["building"] = building
        attrs["organization_id"] = building.organization_id
        attrs["campus_id"] = building.campus_id

        floor_number = attrs.get("floor_number", instance.floor_number if instance else None)
        label = attrs.get("label", instance.label if instance else None)

        # Unique floor_number per building
        if floor_number is not None:
            fn_qs = Floor.all_objects.filter(building=building, floor_number=floor_number)
            if instance:
                fn_qs = fn_qs.exclude(id=instance.id)
            if fn_qs.exists():
                raise serializers.ValidationError({"floor_number": "A floor with this number already exists in this building."})

        # Unique label per building
        if label:
            lbl_qs = Floor.all_objects.filter(building=building, label=label)
            if instance:
                lbl_qs = lbl_qs.exclude(id=instance.id)
            if lbl_qs.exists():
                raise serializers.ValidationError({"label": "A floor with this label already exists in this building."})

        return attrs


class RoomSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    campus_id = serializers.UUIDField(read_only=True)
    building_id = serializers.UUIDField(required=False)
    building_name = serializers.CharField(source="building.name", read_only=True)
    building_code = serializers.CharField(source="building.code", read_only=True)
    floor_id = serializers.UUIDField(required=True)
    floor_label = serializers.CharField(source="floor.label", read_only=True)
    floor_number = serializers.IntegerField(source="floor.floor_number", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id",
            "organization_id",
            "campus_id",
            "building_id",
            "building_name",
            "building_code",
            "floor_id",
            "floor_label",
            "floor_number",
            "room_number",
            "name",
            "room_type",
            "capacity",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "campus_id", "created_at", "updated_at"]

    def validate_room_number(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = getattr(self, "instance", None)

        floor_id = attrs.get("floor_id") or (instance.floor_id if instance else None)
        if not floor_id:
            raise serializers.ValidationError({"floor_id": "Floor is required."})

        try:
            floor_qs = Floor.all_objects.select_related("building").all()
            if user and not user.is_superuser:
                floor_qs = floor_qs.filter(organization_id=user.organization_id)
            floor = floor_qs.get(id=floor_id)
        except Floor.DoesNotExist:
            raise serializers.ValidationError({"floor_id": "Floor not found within your organization."})

        # Check building consistency if building_id provided
        building_id = attrs.get("building_id") or (instance.building_id if instance else None)
        if building_id and str(floor.building_id) != str(building_id):
            raise serializers.ValidationError({"building_id": "Selected floor does not belong to this building."})

        attrs["floor"] = floor
        attrs["building"] = floor.building
        attrs["organization_id"] = floor.organization_id
        attrs["campus_id"] = floor.campus_id

        # Unique room_number per floor
        room_number = attrs.get("room_number", instance.room_number if instance else None)
        if room_number:
            rm_qs = Room.all_objects.filter(floor=floor, room_number=room_number)
            if instance:
                rm_qs = rm_qs.exclude(id=instance.id)
            if rm_qs.exists():
                raise serializers.ValidationError({"room_number": "A room with this number already exists on this floor."})

        return attrs


class AssetSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    campus_id = serializers.UUIDField(required=False)
    department_id = serializers.UUIDField(required=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    building_id = serializers.UUIDField(required=False, allow_null=True)
    building_name = serializers.CharField(source="building.name", read_only=True)
    floor_id = serializers.UUIDField(required=False, allow_null=True)
    floor_label = serializers.CharField(source="floor.label", read_only=True)
    room_id = serializers.UUIDField(required=False, allow_null=True)
    room_number = serializers.CharField(source="room.room_number", read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "organization_id",
            "campus_id",
            "department_id",
            "department_name",
            "building_id",
            "building_name",
            "floor_id",
            "floor_label",
            "room_id",
            "room_number",
            "name",
            "asset_tag",
            "serial_number",
            "category",
            "status",
            "install_date",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]

    def validate_asset_tag(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        instance = getattr(self, "instance", None)

        department_id = attrs.get("department_id") or (instance.department_id if instance else None)
        if not department_id:
            raise serializers.ValidationError({"department_id": "Responsible department is required."})

        try:
            dept_qs = Department.all_objects.all()
            if user and not user.is_superuser:
                dept_qs = dept_qs.filter(organization_id=user.organization_id)
            department = dept_qs.get(id=department_id)
        except Department.DoesNotExist:
            raise serializers.ValidationError({"department_id": "Department not found within your organization."})

        attrs["department"] = department
        attrs["organization_id"] = department.organization_id
        attrs["campus_id"] = department.campus_id

        # Enforce location hierarchy and resolve parent links
        room_id = attrs.get("room_id") if "room_id" in attrs else (instance.room_id if instance else None)
        floor_id = attrs.get("floor_id") if "floor_id" in attrs else (instance.floor_id if instance else None)
        building_id = attrs.get("building_id") if "building_id" in attrs else (instance.building_id if instance else None)

        if room_id:
            try:
                room_qs = Room.all_objects.select_related("floor__building").all()
                if user and not user.is_superuser:
                    room_qs = room_qs.filter(organization_id=user.organization_id)
                room = room_qs.get(id=room_id)
            except Room.DoesNotExist:
                raise serializers.ValidationError({"room_id": "Room not found within your organization."})

            if room.campus_id != department.campus_id:
                raise serializers.ValidationError({"room_id": "Room belongs to a different campus than the department."})

            if floor_id and str(room.floor_id) != str(floor_id):
                raise serializers.ValidationError({"room_id": "Selected room does not belong to the selected floor."})
            if building_id and str(room.building_id) != str(building_id):
                raise serializers.ValidationError({"room_id": "Selected room does not belong to the selected building."})

            attrs["room"] = room
            attrs["floor"] = room.floor
            attrs["building"] = room.building

        elif floor_id:
            try:
                floor_qs = Floor.all_objects.select_related("building").all()
                if user and not user.is_superuser:
                    floor_qs = floor_qs.filter(organization_id=user.organization_id)
                floor = floor_qs.get(id=floor_id)
            except Floor.DoesNotExist:
                raise serializers.ValidationError({"floor_id": "Floor not found within your organization."})

            if floor.campus_id != department.campus_id:
                raise serializers.ValidationError({"floor_id": "Floor belongs to a different campus than the department."})

            if building_id and str(floor.building_id) != str(building_id):
                raise serializers.ValidationError({"floor_id": "Selected floor does not belong to the selected building."})

            attrs["room"] = None
            attrs["floor"] = floor
            attrs["building"] = floor.building

        elif building_id:
            try:
                bldg_qs = Building.all_objects.all()
                if user and not user.is_superuser:
                    bldg_qs = bldg_qs.filter(organization_id=user.organization_id)
                building = bldg_qs.get(id=building_id)
            except Building.DoesNotExist:
                raise serializers.ValidationError({"building_id": "Building not found within your organization."})

            if building.campus_id != department.campus_id:
                raise serializers.ValidationError({"building_id": "Building belongs to a different campus than the department."})

            attrs["room"] = None
            attrs["floor"] = None
            attrs["building"] = building
        else:
            # Standalone asset within department
            if "room_id" in attrs and attrs["room_id"] is None:
                attrs["room"] = None
            if "floor_id" in attrs and attrs["floor_id"] is None:
                attrs["floor"] = None
            if "building_id" in attrs and attrs["building_id"] is None:
                attrs["building"] = None

        # Unique asset tag per campus
        asset_tag = attrs.get("asset_tag", instance.asset_tag if instance else None)
        if asset_tag and attrs["campus_id"]:
            at_qs = Asset.all_objects.filter(campus_id=attrs["campus_id"], asset_tag=asset_tag)
            if instance:
                at_qs = at_qs.exclude(id=instance.id)
            if at_qs.exists():
                raise serializers.ValidationError({"asset_tag": "An asset with this tag already exists on this campus."})

        return attrs
