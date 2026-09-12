"""
Global pytest fixtures for Paraxis AI test suite.
"""
import uuid
import pytest
from rest_framework.test import APIClient
from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus
from core.models.access import Role, Permission
from core.models.user import User
from core.authentication.jwt import generate_access_token, generate_refresh_token
from core.context import clear_tenant_context


@pytest.fixture(autouse=True)
def cleanup_tenant_context():
    """Ensure contextvars are completely clean before and after every test."""
    clear_tenant_context()
    yield
    clear_tenant_context()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org_a(db):
    return Organization.objects.create(
        name="Apex University System",
        slug="apex-univ",
        status=OrganizationStatus.ACTIVE,
    )


@pytest.fixture
def org_b(db):
    return Organization.objects.create(
        name="Beacon College Network",
        slug="beacon-college",
        status=OrganizationStatus.ACTIVE,
    )


@pytest.fixture
def campus_a1(db, org_a):
    return Campus.objects.create(
        organization=org_a,
        name="Apex Engineering Campus",
        code="ENG",
        timezone="UTC",
        status=CampusStatus.ACTIVE,
    )


@pytest.fixture
def campus_a2(db, org_a):
    return Campus.objects.create(
        organization=org_a,
        name="Apex Medical Campus",
        code="MED",
        timezone="UTC",
        status=CampusStatus.ACTIVE,
    )


@pytest.fixture
def campus_b1(db, org_b):
    return Campus.objects.create(
        organization=org_b,
        name="Beacon Central Campus",
        code="MAIN",
        timezone="UTC",
        status=CampusStatus.ACTIVE,
    )


@pytest.fixture
def standard_roles(db):
    role_student, _ = Role.objects.get_or_create(name="STUDENT", is_system_role=True)
    role_faculty, _ = Role.objects.get_or_create(name="FACULTY", is_system_role=True)
    role_admin, _ = Role.objects.get_or_create(name="CAMPUS_ADMIN", is_system_role=True)
    role_super, _ = Role.objects.get_or_create(name="SUPER_ADMIN", is_system_role=True)

    perm_incident_create, _ = Permission.objects.get_or_create(
        codename="incident:create", defaults={"name": "Create incident", "module": "incident"}
    )
    perm_campus_manage, _ = Permission.objects.get_or_create(
        codename="campus:manage", defaults={"name": "Manage campuses", "module": "admin"}
    )

    role_student.permissions.add(perm_incident_create)
    role_admin.permissions.add(perm_incident_create, perm_campus_manage)
    role_super.permissions.add(perm_incident_create, perm_campus_manage)

    return {
        "STUDENT": role_student,
        "FACULTY": role_faculty,
        "CAMPUS_ADMIN": role_admin,
        "SUPER_ADMIN": role_super,
    }


@pytest.fixture
def user_student_a(db, org_a, campus_a1, standard_roles):
    user = User.objects.create_user(
        email="student.a@apex.edu",
        full_name="Student Alpha",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a1,
    )
    user.roles.add(standard_roles["STUDENT"])
    return user


@pytest.fixture
def user_admin_a(db, org_a, campus_a1, standard_roles):
    user = User.objects.create_user(
        email="admin.a@apex.edu",
        full_name="Admin Alpha",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a1,
    )
    user.roles.add(standard_roles["CAMPUS_ADMIN"])
    return user


@pytest.fixture
def user_super(db, standard_roles):
    user = User.objects.create_superuser(
        email="superadmin@paraxis.ai",
        full_name="Platform Superadmin",
        password="SuperPassword123!",
    )
    user.roles.add(standard_roles["SUPER_ADMIN"])
    return user


@pytest.fixture
def user_student_b(db, org_b, campus_b1, standard_roles):
    user = User.objects.create_user(
        email="student.b@beacon.edu",
        full_name="Student Beta",
        password="TestPassword123!",
        organization=org_b,
        primary_campus=campus_b1,
    )
    user.roles.add(standard_roles["STUDENT"])
    return user


@pytest.fixture
def auth_headers_student_a(user_student_a, campus_a1):
    token = generate_access_token(user_student_a, campus_id=campus_a1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin_a(user_admin_a, campus_a1):
    token = generate_access_token(user_admin_a, campus_id=campus_a1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def auth_headers_super(user_super):
    token = generate_access_token(user_super)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def auth_headers_student_b(user_student_b, campus_b1):
    token = generate_access_token(user_student_b, campus_id=campus_b1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
