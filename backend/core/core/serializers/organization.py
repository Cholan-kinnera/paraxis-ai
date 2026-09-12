"""
Serializers for Organization and Campus management.
"""
from rest_framework import serializers
from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer for Organization model.
    """
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        slug = value.strip().lower()
        instance = getattr(self, "instance", None)
        qs = Organization.objects.filter(slug=slug)
        if instance:
            qs = qs.exclude(id=instance.id)
        if qs.exists():
            raise serializers.ValidationError("An organization with this slug already exists.")
        return slug


class CampusSerializer(serializers.ModelSerializer):
    """
    Serializer for Campus model.
    Enforces that non-superusers cannot bind campuses to other organizations.
    """
    organization_id = serializers.UUIDField(required=False)

    class Meta:
        model = Campus
        fields = [
            "id",
            "organization_id",
            "name",
            "code",
            "timezone",
            "address",
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

        org_id = attrs.get("organization_id")
        if not org_id and user:
            org_id = user.organization_id
            attrs["organization_id"] = org_id

        if not org_id and instance:
            org_id = instance.organization_id

        if not org_id:
            raise serializers.ValidationError({"organization_id": "Organization is required."})

        # Non-superusers can only manage campuses in their own organization
        if user and not user.is_superuser:
            if str(org_id) != str(user.organization_id):
                raise serializers.ValidationError({"organization_id": "You cannot manage campuses outside your organization."})

        # Validate code uniqueness within organization
        code = attrs.get("code") or (instance.code if instance else None)
        if code and org_id:
            qs = Campus.objects.filter(organization_id=org_id, code=code)
            if instance:
                qs = qs.exclude(id=instance.id)
            if qs.exists():
                raise serializers.ValidationError({"code": "A campus with this code already exists in this organization."})

        return attrs
