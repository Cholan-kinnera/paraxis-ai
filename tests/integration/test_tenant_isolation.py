"""
Integration tests for Strict Multi-Tenant Isolation and Data Segregation.
Ensures zero cross-tenant leakage across Organizations and Campuses.
"""
import uuid
import pytest
from core.context import (
    get_current_organization_id,
    get_current_campus_id,
    set_current_tenant,
    clear_tenant_context,
)
from core.models.organization import Campus, Organization
from core.models.base import TenantScopedModel


@pytest.mark.django_db
def test_cross_org_campus_lookup_returns_404(api_client, auth_headers_student_a, campus_b1):
    """
    Test user in Org A attempting to access Campus B1 in Org B receives 404 (zero existence leakage).
    """
    url = f"/api/v1/campuses/{campus_b1.id}/"
    response = api_client.get(url, **auth_headers_student_a)
    assert response.status_code == 404
    assert response.json()["error"]["code"] in ["RESOURCE_NOT_FOUND", "TENANT_NOT_FOUND"]


@pytest.mark.django_db
def test_cross_org_organization_lookup_returns_404(api_client, auth_headers_student_a, org_b):
    """
    Test user in Org A attempting to access Org B receives 404.
    """
    url = f"/api/v1/organizations/{org_b.id}/"
    response = api_client.get(url, **auth_headers_student_a)
    assert response.status_code == 404


@pytest.mark.django_db
def test_campus_list_only_returns_own_organization_campuses(
    api_client, auth_headers_student_a, org_a, campus_a1, campus_a2, campus_b1
):
    """
    Test GET /api/v1/campuses/ returns campuses for caller's org only, excluding other organizations.
    """
    response = api_client.get("/api/v1/campuses/", **auth_headers_student_a)
    assert response.status_code == 200
    campuses = response.json()
    campus_ids = [c["id"] for c in campuses]

    assert str(campus_a1.id) in campus_ids
    assert str(campus_a2.id) in campus_ids
    assert str(campus_b1.id) not in campus_ids


@pytest.mark.django_db
def test_login_with_cross_org_campus_rejected(api_client, user_student_a, campus_b1):
    """
    Test authenticating with a campus_id that belongs to another organization fails.
    """
    url = "/api/v1/auth/token/"
    payload = {
        "email": user_student_a.email,
        "password": "TestPassword123!",
        "campus_id": str(campus_b1.id),
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 401
    assert response.json()["error"]["code"] in ["TENANT_NOT_FOUND", "UNAUTHENTICATED"]


@pytest.mark.django_db
def test_tenant_context_cleaned_after_request(api_client, auth_headers_student_a):
    """
    Test that request contextvars are unconditionally cleared once the request completes.
    """
    assert get_current_organization_id() is None
    assert get_current_campus_id() is None

    response = api_client.get("/api/v1/auth/me/", **auth_headers_student_a)
    assert response.status_code == 200

    # Must be None immediately after response is delivered
    assert get_current_organization_id() is None
    assert get_current_campus_id() is None


@pytest.mark.django_db
def test_tampered_payload_campus_cannot_escape_tenant(
    api_client, auth_headers_admin_a, org_b
):
    """
    Test that an attacker passing organization_id of another institution in POST /campuses/
    is stopped and denied.
    """
    payload = {
        "organization_id": str(org_b.id),
        "name": "Malicious Campus Injection",
        "code": "MAL",
        "timezone": "UTC",
    }
    response = api_client.post("/api/v1/campuses/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
