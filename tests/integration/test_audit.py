"""
Integration tests for Immutable Audit Logging and Compliance Tracking.
Adheres to ADR-007 immutability guarantees.
"""
import pytest
from core.models.audit import AuditLog, AuditLogImmutableError
from core.services.audit import log_audit_event


@pytest.mark.django_db
def test_login_creates_audit_log(api_client, user_student_a, campus_a1):
    """Test successful authentication produces an audit log record."""
    initial_count = AuditLog.objects.filter(action="auth.login").count()

    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": user_student_a.email, "password": "TestPassword123!", "campus_id": str(campus_a1.id)},
        format="json",
    )
    assert response.status_code == 200

    new_count = AuditLog.objects.filter(action="auth.login").count()
    assert new_count == initial_count + 1

    audit_entry = AuditLog.objects.filter(action="auth.login").latest("created_at")
    assert str(audit_entry.actor_id) == str(user_student_a.id)
    assert str(audit_entry.organization_id) == str(user_student_a.organization_id)


@pytest.mark.django_db
def test_failed_login_creates_audit_log(api_client, user_student_a):
    """Test failed authentication produces an audit log record."""
    initial_count = AuditLog.objects.filter(action="auth.login_failed").count()

    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": user_student_a.email, "password": "BadPassword!"},
        format="json",
    )
    assert response.status_code == 401

    new_count = AuditLog.objects.filter(action="auth.login_failed").count()
    assert new_count == initial_count + 1


@pytest.mark.django_db
def test_audit_log_record_cannot_be_updated(org_a, campus_a1, user_student_a):
    """Test AuditLog immutability: UPDATE operations are strictly prohibited."""
    log = log_audit_event(
        action="test.action",
        entity_type="Campus",
        entity_id=str(campus_a1.id),
        actor=user_student_a,
        organization=org_a,
        campus=campus_a1,
    )

    # Attempt to mutate and save
    log.action = "tampered.action"
    with pytest.raises(AuditLogImmutableError):
        log.save()


@pytest.mark.django_db
def test_audit_log_record_cannot_be_deleted(org_a, campus_a1, user_student_a):
    """Test AuditLog immutability: DELETE operations are strictly prohibited."""
    log = log_audit_event(
        action="test.action",
        entity_type="Campus",
        entity_id=str(campus_a1.id),
        actor=user_student_a,
        organization=org_a,
        campus=campus_a1,
    )

    with pytest.raises(AuditLogImmutableError):
        log.delete()


@pytest.mark.django_db
def test_audit_log_queryset_bulk_update_and_delete_prohibited(org_a, campus_a1, user_student_a):
    """Test AuditLogManager prohibits bulk update and delete."""
    log_audit_event(
        action="bulk.test",
        entity_type="Campus",
        entity_id=str(campus_a1.id),
        actor=user_student_a,
        organization=org_a,
    )

    with pytest.raises(AuditLogImmutableError):
        AuditLog.objects.filter(action="bulk.test").update(action="tampered")

    with pytest.raises(AuditLogImmutableError):
        AuditLog.objects.filter(action="bulk.test").delete()
