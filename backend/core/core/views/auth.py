"""
Authentication API views for Paraxis AI.
Implements token issuance, token rotation, user profile endpoint, and audit event logging.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed
from core.serializers.auth import (
    TokenObtainSerializer,
    TokenRefreshSerializer,
    UserProfileSerializer,
)
from core.permissions.rbac import IsAuthenticatedUser
from core.services.audit import log_audit_event


class TokenObtainView(APIView):
    """
    POST /api/v1/auth/token/
    Issue JWT access token (15 min) and refresh token (7 days).
    Records security audit events for both successful and failed authentication attempts.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenObtainSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
            result = serializer.validated_data

            # Record successful login audit event
            user_data = result["user"]
            log_audit_event(
                action="auth.login",
                entity_type="User",
                entity_id=user_data["id"],
                actor=user_data["id"],
                organization=user_data.get("organization_id"),
                campus=user_data.get("campus_id"),
                request=request,
                post_state={"email": user_data["email"]},
            )
            return Response(result, status=status.HTTP_200_OK)
        except AuthenticationFailed as exc:
            # Record failed login audit event
            email = request.data.get("email", "unknown")
            log_audit_event(
                action="auth.login_failed",
                entity_type="User",
                entity_id="anonymous",
                request=request,
                post_state={"attempted_email": str(email)[:100], "reason": str(exc.detail)},
            )
            raise exc


class TokenRefreshView(APIView):
    """
    POST /api/v1/auth/refresh/
    Rotate refresh token and issue a fresh access token.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    GET /api/v1/auth/me/
    Retrieve authenticated caller's profile, roles, permissions, and active tenant context.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
