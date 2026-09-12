"""
Integration tests for JWT Authentication, Token Rotation, and Identity Verification.
"""
from datetime import datetime, timedelta, timezone
import uuid
import jwt
import pytest
from core.models.user import User
from core.authentication.jwt import (
    generate_access_token,
    generate_refresh_token,
    get_jwt_secret,
)


@pytest.mark.django_db
def test_valid_login_returns_token_pair(api_client, user_student_a, campus_a1):
    """Test standard login returns valid access and refresh tokens with correct payload."""
    url = "/api/v1/auth/token/"
    payload = {
        "email": user_student_a.email,
        "password": "TestPassword123!",
        "campus_id": str(campus_a1.id),
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data
    assert data["user"]["email"] == user_student_a.email
    assert data["user"]["organization_id"] == str(user_student_a.organization_id)
    assert data["user"]["campus_id"] == str(campus_a1.id)
    assert "STUDENT" in data["user"]["roles"]


@pytest.mark.django_db
def test_login_invalid_password_fails(api_client, user_student_a):
    """Test wrong password fails with UNAUTHENTICATED error."""
    url = "/api/v1/auth/token/"
    payload = {
        "email": user_student_a.email,
        "password": "WrongPassword123!",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_login_inactive_user_rejected(api_client, user_student_a):
    """Test deactivated user cannot obtain tokens."""
    user_student_a.is_active = False
    user_student_a.save()

    url = "/api/v1/auth/token/"
    payload = {
        "email": user_student_a.email,
        "password": "TestPassword123!",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_expired_token_rejected(api_client, user_student_a, campus_a1):
    """Test expired access token is rejected by protected endpoints."""
    # Forge expired token
    now = datetime.now(timezone.utc) - timedelta(hours=2)
    payload = {
        "sub": str(user_student_a.id),
        "email": user_student_a.email,
        "org_id": str(user_student_a.organization_id),
        "campus_id": str(campus_a1.id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    expired_token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")

    response = api_client.get("/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {expired_token}")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_tampered_signature_token_rejected(api_client, user_student_a, campus_a1):
    """Test token signed with wrong secret key is rejected."""
    token = generate_access_token(user_student_a, campus_id=campus_a1.id)
    # Forge token with arbitrary secret
    fake_token = jwt.encode(
        jwt.decode(token, options={"verify_signature": False}),
        "forged-secret-key-attacker-attempt",
        algorithm="HS256",
    )

    response = api_client.get("/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {fake_token}")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_wrong_token_type_rejected(api_client, user_student_a, campus_a1):
    """Test that a refresh token cannot be used to authenticate API requests directly."""
    refresh_token = generate_refresh_token(user_student_a, campus_id=campus_a1.id)

    response = api_client.get("/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {refresh_token}")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_auth_me_endpoint_returns_caller_profile(api_client, auth_headers_student_a, user_student_a, campus_a1):
    """Test GET /api/v1/auth/me/ returns verified identity, tenant context, and permissions."""
    response = api_client.get("/api/v1/auth/me/", **auth_headers_student_a)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_student_a.email
    assert data["full_name"] == user_student_a.full_name
    assert data["organization"]["slug"] == user_student_a.organization.slug
    assert data["primary_campus"]["code"] == campus_a1.code
    assert "STUDENT" in data["roles"]
    assert "incident:create" in data["permissions"]
    assert data["active_tenant_context"]["organization_id"] == str(user_student_a.organization_id)
    assert data["active_tenant_context"]["campus_id"] == str(campus_a1.id)


@pytest.mark.django_db
def test_token_refresh_rotation(api_client, user_student_a, campus_a1):
    """Test refresh token yields a new rotated access and refresh token pair."""
    refresh_token = generate_refresh_token(user_student_a, campus_id=campus_a1.id)

    response = api_client.post("/api/v1/auth/refresh/", {"refresh": refresh_token}, format="json")
    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data

    # Verify newly issued access token works
    new_access = data["access"]
    me_resp = api_client.get("/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {new_access}")
    assert me_resp.status_code == 200
