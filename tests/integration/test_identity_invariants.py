"""
Integration tests for Identity Domain Invariants and Model Constraints.
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pytest
from core.models.organization import Campus, Organization
from core.models.access import Role
from core.models.user import User


@pytest.mark.django_db
def test_user_cannot_have_mismatched_primary_campus(org_a, org_b, campus_b1):
    """
    Test invariant: Campus.organization != User.organization is invalid.
    Must raise ValidationError.
    """
    with pytest.raises(ValidationError):
        User.objects.create_user(
            email="mismatch@apex.edu",
            full_name="Mismatch User",
            password="Password123!",
            organization=org_a,
            primary_campus=campus_b1,  # Belongs to org_b!
        )


@pytest.mark.django_db
def test_campus_code_unique_per_organization(org_a, campus_a1):
    """
    Test campus code uniqueness within the same organization.
    """
    with pytest.raises(IntegrityError):
        Campus.objects.create(
            organization=org_a,
            name="Duplicate Code Campus",
            code=campus_a1.code,  # 'ENG' already exists in org_a!
            timezone="UTC",
        )


@pytest.mark.django_db
def test_campus_code_can_be_reused_across_different_organizations(org_a, org_b, campus_a1):
    """
    Test campus code 'ENG' can coexist across distinct organizations.
    """
    campus_b_eng = Campus.objects.create(
        organization=org_b,
        name="Beacon Engineering Campus",
        code=campus_a1.code,  # 'ENG'
        timezone="UTC",
    )
    assert campus_b_eng.id is not None
    assert campus_b_eng.code == campus_a1.code


@pytest.mark.django_db
def test_email_unique_per_organization(org_a, user_student_a):
    """
    Test duplicate email in the same organization raises IntegrityError.
    """
    with pytest.raises((IntegrityError, ValidationError)):
        User.objects.create_user(
            email=user_student_a.email,
            full_name="Duplicate Email User",
            password="Password123!",
            organization=org_a,
        )


@pytest.mark.django_db
def test_email_can_coexist_across_different_organizations(org_a, org_b, user_student_a):
    """
    Test the same email address can exist across different institutional tenants.
    """
    user_b = User.objects.create_user(
        email=user_student_a.email,
        full_name="Same Email in Org B",
        password="Password123!",
        organization=org_b,
    )
    assert user_b.id != user_student_a.id
    assert user_b.email == user_student_a.email


@pytest.mark.django_db
def test_system_role_cannot_be_deleted(standard_roles):
    """
    Test that protected system roles cannot be deleted.
    """
    student_role = standard_roles["STUDENT"]
    with pytest.raises(ValidationError):
        student_role.delete()


@pytest.mark.django_db
def test_system_role_cannot_be_bound_to_organization(org_a):
    """
    Test invariant: System roles must not be bound to a specific organization.
    """
    role = Role(
        name="INVALID_SYS_ROLE",
        is_system_role=True,
        organization=org_a,
    )
    with pytest.raises(ValidationError):
        role.clean()
