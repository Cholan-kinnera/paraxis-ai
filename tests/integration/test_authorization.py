"""
Integration tests for Role-Based Access Control (RBAC) and Privileged Operations.
"""
import pytest
from core.models.organization import OrganizationStatus
from core.models.access import Role


@pytest.mark.django_db
def test_unauthenticated_request_rejected(api_client):
    """Test unauthenticated call to protected endpoint returns 401 UNAUTHENTICATED."""
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.django_db
def test_student_cannot_create_campus(api_client, auth_headers_student_a):
    """Test student role is forbidden from provisioning campuses."""
    payload = {
        "name": "Unauthorized Campus",
        "code": "UNAUTH",
        "timezone": "UTC",
    }
    response = api_client.post("/api/v1/campuses/", payload, format="json", **auth_headers_student_a)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_campus_admin_can_create_campus(api_client, auth_headers_admin_a, org_a):
    """Test Campus Admin can provision a campus within their organization."""
    payload = {
        "name": "North Annex Campus",
        "code": "ANNEX",
        "timezone": "UTC",
    }
    response = api_client.post("/api/v1/campuses/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "North Annex Campus"
    assert data["code"] == "ANNEX"
    assert data["organization_id"] == str(org_a.id)


@pytest.mark.django_db
def test_campus_admin_cannot_create_organization(api_client, auth_headers_admin_a):
    """Test Campus Admin cannot provision new institutional organizations (Super Admin only)."""
    payload = {
        "name": "Apex Rival Trust",
        "slug": "apex-rival",
        "status": "ACTIVE",
    }
    response = api_client.post("/api/v1/organizations/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_super_admin_can_create_organization(api_client, auth_headers_super):
    """Test Platform Super Administrator can provision new organizations."""
    payload = {
        "name": "Crestview University System",
        "slug": "crestview-univ",
        "status": "ACTIVE",
    }
    response = api_client.post("/api/v1/organizations/", payload, format="json", **auth_headers_super)
    assert response.status_code == 201
    assert response.json()["slug"] == "crestview-univ"
