"""
Integration tests for Strict Multi-Tenant Isolation and Data Segregation.
Ensures zero cross-tenant leakage across Organizations and Campuses.
"""
import uuid
import pytest
from django.db import connection, models
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


# ---------------------------------------------------------------------------
# TenantScopedManager Fail-Closed Verification
# ---------------------------------------------------------------------------


class MockTenantEntity(TenantScopedModel):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "core"
        db_table = "test_mock_tenant_entity"


class MockCampusScopedEntity(TenantScopedModel):
    name = models.CharField(max_length=100)
    campus_scoped = True

    class Meta:
        app_label = "core"
        db_table = "test_mock_campus_scoped_entity"


@pytest.fixture(scope="module")
def mock_tenant_tables(django_db_setup, django_db_blocker):
    """Create dynamic tables once per module for testing TenantScopedModel in PostgreSQL."""
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            editor.create_model(MockTenantEntity)
            editor.create_model(MockCampusScopedEntity)
        yield
        with connection.schema_editor() as editor:
            editor.delete_model(MockCampusScopedEntity)
            editor.delete_model(MockTenantEntity)


@pytest.mark.django_db
def test_tenant_scoped_manager_with_no_organization_context_returns_no_records(
    mock_tenant_tables, org_a, org_b
):
    """
    Test 1: TenantScopedManager with no organization context returns no records.
    Guarantees fail-closed isolation when tenant context is missing.
    """
    MockTenantEntity.all_objects.create(organization=org_a, name="Org A Resource")
    MockTenantEntity.all_objects.create(organization=org_b, name="Org B Resource")

    clear_tenant_context()
    assert get_current_organization_id() is None

    # Query through TenantScopedManager with no tenant context
    qs = MockTenantEntity.objects.all()
    assert qs.count() == 0
    assert list(qs) == []


@pytest.mark.django_db
def test_tenant_scoped_manager_with_valid_organization_context_returns_only_own_records(
    mock_tenant_tables, org_a, org_b
):
    """
    Test 2: TenantScopedManager with valid organization context returns only that
    organization's records.
    """
    item_a = MockTenantEntity.all_objects.create(organization=org_a, name="Org A Resource")
    item_b = MockTenantEntity.all_objects.create(organization=org_b, name="Org B Resource")

    # Scope to Org A
    set_current_tenant(org_a.id)
    qs_a = MockTenantEntity.objects.all()
    assert qs_a.count() == 1
    assert qs_a.first().id == item_a.id
    assert qs_a.first().name == "Org A Resource"

    # Scope to Org B
    set_current_tenant(org_b.id)
    qs_b = MockTenantEntity.objects.all()
    assert qs_b.count() == 1
    assert qs_b.first().id == item_b.id
    assert qs_b.first().name == "Org B Resource"


@pytest.mark.django_db
def test_campus_scoped_behavior_cannot_return_another_campus_records(
    mock_tenant_tables, org_a, campus_a1, campus_a2
):
    """
    Test 3: Campus-scoped behavior cannot return another campus's records.
    """
    item_c1 = MockTenantEntity.all_objects.create(
        organization=org_a, campus=campus_a1, name="Campus A1 Resource"
    )
    item_c2 = MockTenantEntity.all_objects.create(
        organization=org_a, campus=campus_a2, name="Campus A2 Resource"
    )

    # Scope to Campus A1
    set_current_tenant(org_a.id, campus_a1.id)
    qs_c1 = MockTenantEntity.objects.all()
    assert qs_c1.count() == 1
    assert qs_c1.first().id == item_c1.id
    assert qs_c1.first().name == "Campus A1 Resource"

    # Scope to Campus A2
    set_current_tenant(org_a.id, campus_a2.id)
    qs_c2 = MockTenantEntity.objects.all()
    assert qs_c2.count() == 1
    assert qs_c2.first().id == item_c2.id
    assert qs_c2.first().name == "Campus A2 Resource"


@pytest.mark.django_db
def test_campus_scoped_model_fails_closed_without_campus_context(
    mock_tenant_tables, org_a, campus_a1
):
    """
    Test 4: A model requiring campus scope (campus_scoped=True) fails closed
    when campus context is missing, even if organization context is present.
    """
    MockCampusScopedEntity.all_objects.create(
        organization=org_a, campus=campus_a1, name="Strictly Campus Scoped"
    )

    # Set organization context only (no campus context)
    set_current_tenant(org_a.id, campus_id=None)
    qs = MockCampusScopedEntity.objects.all()
    assert qs.count() == 0
    assert list(qs) == []

    # Provide campus context
    set_current_tenant(org_a.id, campus_id=campus_a1.id)
    qs_scoped = MockCampusScopedEntity.objects.all()
    assert qs_scoped.count() == 1
    assert qs_scoped.first().name == "Strictly Campus Scoped"


@pytest.mark.django_db
def test_context_cleanup_prevents_manager_leakage_after_api_request(
    api_client, auth_headers_student_a, mock_tenant_tables, org_a
):
    """
    Test 5: Context cleanup guarantees TenantScopedManager immediately fails closed
    after an HTTP request completes.
    """
    MockTenantEntity.all_objects.create(organization=org_a, name="Org A Resource")

    # Context is clean before request
    assert get_current_organization_id() is None
    assert MockTenantEntity.objects.all().count() == 0

    # Perform API request
    response = api_client.get("/api/v1/auth/me/", **auth_headers_student_a)
    assert response.status_code == 200

    # Context must be clean after request
    assert get_current_organization_id() is None
    assert MockTenantEntity.objects.all().count() == 0
