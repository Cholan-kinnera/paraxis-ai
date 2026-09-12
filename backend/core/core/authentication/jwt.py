"""
JWT Authentication and token lifecycle management for Paraxis AI.
Complies with docs/api/authentication.md specifications:
- Access tokens: 15-minute validity, HS256, carrying sub, email, org_id, campus_id, roles.
- Refresh tokens: 7-day validity, revocable, type-enforced.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
import jwt
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from core.context import set_current_tenant, set_current_actor_id
from core.models.user import User
from core.models.organization import Campus


def get_jwt_secret() -> str:
    return getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)


def generate_access_token(user: User, campus_id: Optional[uuid.UUID] = None) -> str:
    """
    Issue short-lived (15 min) JWT access token with tenant and role claims.
    """
    now = datetime.now(timezone.utc)
    lifetime = getattr(settings, "JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 15)
    exp = now + timedelta(minutes=lifetime)

    active_campus_id = campus_id or user.primary_campus_id
    role_names = user.get_role_names()

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "org_id": str(user.organization_id) if user.organization_id else None,
        "campus_id": str(active_campus_id) if active_campus_id else None,
        "roles": role_names,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def generate_refresh_token(user: User, campus_id: Optional[uuid.UUID] = None) -> str:
    """
    Issue long-lived (7 days) refresh token with unique jti for rotation.
    """
    now = datetime.now(timezone.utc)
    lifetime = getattr(settings, "JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7)
    exp = now + timedelta(days=lifetime)

    active_campus_id = campus_id or user.primary_campus_id

    payload = {
        "sub": str(user.id),
        "org_id": str(user.organization_id) if user.organization_id else None,
        "campus_id": str(active_campus_id) if active_campus_id else None,
        "jti": uuid.uuid4().hex,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def decode_token(token_str: str, expected_type: str = "access") -> dict:
    """
    Verify signature, expiration, and payload invariants of a JWT.
    """
    try:
        payload = jwt.decode(
            token_str,
            get_jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Authentication token has expired.", code="UNAUTHENTICATED")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid authentication token.", code="UNAUTHENTICATED")

    token_type = payload.get("type")
    if token_type != expected_type:
        raise AuthenticationFailed(
            f"Invalid token type: expected '{expected_type}', got '{token_type}'.",
            code="UNAUTHENTICATED",
        )
    return payload


class JWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class validating Bearer JWTs and establishing verified tenant context.
    """

    def authenticate(self, request) -> Optional[Tuple[User, dict]]:
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        payload = decode_token(token, expected_type="access")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationFailed("Token missing user subject claim.", code="UNAUTHENTICATED")

        try:
            user_id = uuid.UUID(user_id_str)
            user = (
                User.objects.select_related("organization", "primary_campus")
                .prefetch_related("roles__permissions")
                .get(id=user_id)
            )
        except (ValueError, User.DoesNotExist):
            raise AuthenticationFailed("User identified by token does not exist.", code="UNAUTHENTICATED")

        if not user.is_active:
            raise AuthenticationFailed("User account is suspended or inactive.", code="UNAUTHENTICATED")

        # Derive and validate active tenant context
        token_org_id = payload.get("org_id")
        if token_org_id:
            try:
                token_org_uuid = uuid.UUID(token_org_id)
                if user.organization_id and user.organization_id != token_org_uuid:
                    raise AuthenticationFailed("Token organization claim mismatch.", code="PERMISSION_DENIED")
            except ValueError:
                raise AuthenticationFailed("Invalid organization claim format.", code="UNAUTHENTICATED")

        # Determine campus context
        active_campus_id = None
        token_campus_id = payload.get("campus_id")
        if token_campus_id:
            try:
                campus_uuid = uuid.UUID(token_campus_id)
                # Verify campus exists and belongs to user's organization
                if user.is_superuser:
                    active_campus_id = campus_uuid
                elif Campus.objects.filter(id=campus_uuid, organization_id=user.organization_id).exists():
                    active_campus_id = campus_uuid
                else:
                    raise AuthenticationFailed("Requested campus is invalid or outside tenant bounds.", code="TENANT_NOT_FOUND")
            except ValueError:
                raise AuthenticationFailed("Invalid campus claim format.", code="UNAUTHENTICATED")
        else:
            active_campus_id = user.primary_campus_id

        # Establish verified tenant context for the duration of this request
        set_current_tenant(user.organization_id, active_campus_id)
        set_current_actor_id(user.id)

        # Attach active tenant properties to request
        request.active_organization_id = user.organization_id
        request.active_campus_id = active_campus_id

        return user, payload

    def authenticate_header(self, request) -> str:
        return 'Bearer realm="api"'
