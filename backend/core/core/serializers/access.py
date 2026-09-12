"""
Serializers for Role and Permission RBAC models.
"""
from rest_framework import serializers
from core.models.access import Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Permission capability model.
    """
    class Meta:
        model = Permission
        fields = [
            "id",
            "codename",
            "name",
            "module",
        ]
        read_only_fields = fields


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for Role model.
    Exposes permissions codenames and prevents tampering with system roles.
    """
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_codenames = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "organization_id",
            "name",
            "description",
            "is_system_role",
            "permissions",
            "permission_codenames",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system_role", "created_at", "updated_at"]
