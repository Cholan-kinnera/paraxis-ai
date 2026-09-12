"""
Authentication serializers for Paraxis AI Core Platform.
Protects sensitive fields and guarantees secure token issuance and rotation.
"""
import uuid
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from core.models.user import User
from core.models.organization import Campus
from core.authentication.jwt import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
)
from core.context import get_current_organization_id, get_current_campus_id


class TokenObtainSerializer(serializers.Serializer):
    """
    Validates user credentials and issues short-lived access and revocable refresh tokens.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    campus_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")
        campus_id = attrs.get("campus_id")

        # Find user by email
        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            raise AuthenticationFailed("Invalid email or password.", code="UNAUTHENTICATED")

        if not user.is_active:
            raise AuthenticationFailed("User account is inactive.", code="UNAUTHENTICATED")

        # If campus_id provided, verify relationship
        target_campus_id = campus_id or user.primary_campus_id
        if target_campus_id:
            if not user.is_superuser:
                campus_exists = Campus.objects.filter(
                    id=target_campus_id, organization_id=user.organization_id
                ).exists()
                if not campus_exists:
                    raise AuthenticationFailed("Target campus is not part of the user's organization.", code="TENANT_NOT_FOUND")

        access_token = generate_access_token(user, campus_id=target_campus_id)
        refresh_token = generate_refresh_token(user, campus_id=target_campus_id)

        return {
            "access": access_token,
            "refresh": refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "roles": user.get_role_names(),
                "organization_id": str(user.organization_id) if user.organization_id else None,
                "campus_id": str(target_campus_id) if target_campus_id else None,
            },
        }


class TokenRefreshSerializer(serializers.Serializer):
    """
    Validates refresh token and issues a fresh rotated access and refresh token pair.
    """
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        refresh_token = attrs.get("refresh")
        payload = decode_token(refresh_token, expected_type="refresh")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationFailed("Invalid refresh token payload.", code="UNAUTHENTICATED")

        try:
            user = User.objects.get(id=uuid.UUID(user_id_str), is_active=True)
        except (ValueError, User.DoesNotExist):
            raise AuthenticationFailed("User account associated with token is not active.", code="UNAUTHENTICATED")

        # Extract campus context if set
        campus_id_str = payload.get("campus_id")
        campus_uuid = uuid.UUID(campus_id_str) if campus_id_str else None

        new_access = generate_access_token(user, campus_id=campus_uuid)
        new_refresh = generate_refresh_token(user, campus_id=campus_uuid)

        return {
            "access": new_access,
            "refresh": new_refresh,
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Safe output serializer for current authenticated user profile.
    """
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    primary_campus = serializers.SerializerMethodField()
    active_tenant_context = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "organization",
            "primary_campus",
            "roles",
            "permissions",
            "active_tenant_context",
            "created_at",
        ]
        read_only_fields = fields

    def get_roles(self, obj: User) -> list:
        return obj.get_role_names()

    def get_permissions(self, obj: User) -> list:
        return obj.get_permission_codenames()

    def get_organization(self, obj: User):
        if not obj.organization:
            return None
        return {
            "id": str(obj.organization.id),
            "name": obj.organization.name,
            "slug": obj.organization.slug,
            "status": obj.organization.status,
        }

    def get_primary_campus(self, obj: User):
        if not obj.primary_campus:
            return None
        return {
            "id": str(obj.primary_campus.id),
            "name": obj.primary_campus.name,
            "code": obj.primary_campus.code,
            "status": obj.primary_campus.status,
        }

    def get_active_tenant_context(self, obj: User) -> dict:
        return {
            "organization_id": str(get_current_organization_id()) if get_current_organization_id() else None,
            "campus_id": str(get_current_campus_id()) if get_current_campus_id() else None,
        }
