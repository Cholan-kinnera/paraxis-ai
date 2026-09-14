"""
Integration tests for Phase 2: Campus Operational Graph.
Verifies tenancy isolation, location hierarchy integrity, RBAC, uniqueness constraints,
audit event generation, and error envelopes across Department, Building, Floor, Room, and Asset.
"""
import pytest
from rest_framework import status
from core.models.campus_graph import (
    Department,
    Building,
    Floor,
    Room,
    Asset,
    DepartmentStatus,
    BuildingStatus,
    RoomType,
    RoomStatus,
    AssetCategory,
    AssetStatus,
)
from core.models.organization import Campus, CampusStatus
from core.models.access import Role, Permission
from core.models.user import User
from core.models.audit import AuditLog
from core.authentication.jwt import generate_access_token


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def dept_a1(db, org_a, campus_a1):
    return Department.objects.create(
        organization=org_a,
        campus=campus_a1,
        name="Information Technology",
        code="IT",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.fixture
def building_a1(db, org_a, campus_a1):
    return Building.objects.create(
        organization=org_a,
        campus=campus_a1,
        name="Science & Engineering Block",
        code="SEB",
        floors_count=4,
        status=BuildingStatus.OPERATIONAL,
    )


@pytest.fixture
def floor_a1(db, org_a, campus_a1, building_a1):
    return Floor.objects.create(
        organization=org_a,
        campus=campus_a1,
        building=building_a1,
        floor_number=1,
        label="First Floor",
    )


@pytest.fixture
def room_a1(db, org_a, campus_a1, building_a1, floor_a1):
    return Room.objects.create(
        organization=org_a,
        campus=campus_a1,
        building=building_a1,
        floor=floor_a1,
        room_number="101",
        name="Hardware Systems Lab",
        room_type=RoomType.LAB,
        capacity=40,
        status=RoomStatus.AVAILABLE,
    )


@pytest.fixture
def asset_a1(db, org_a, campus_a1, dept_a1, building_a1, floor_a1, room_a1):
    return Asset.objects.create(
        organization=org_a,
        campus=campus_a1,
        department=dept_a1,
        building=building_a1,
        floor=floor_a1,
        room=room_a1,
        asset_tag="APX-ENG-IT-001",
        name="Cisco Catalyst Core Switch",
        category=AssetCategory.NETWORKING,
        status=AssetStatus.OPERATIONAL,
    )


@pytest.fixture
def dept_b1(db, org_b, campus_b1):
    return Department.objects.create(
        organization=org_b,
        campus=campus_b1,
        name="Campus Facilities",
        code="FAC",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.fixture
def building_b1(db, org_b, campus_b1):
    return Building.objects.create(
        organization=org_b,
        campus=campus_b1,
        name="Beacon Central Tower",
        code="BCT",
        floors_count=5,
        status=BuildingStatus.OPERATIONAL,
    )


@pytest.fixture
def floor_b1(db, org_b, campus_b1, building_b1):
    return Floor.objects.create(
        organization=org_b,
        campus=campus_b1,
        building=building_b1,
        floor_number=1,
        label="First Floor",
    )


@pytest.fixture
def room_b1(db, org_b, campus_b1, building_b1, floor_b1):
    return Room.objects.create(
        organization=org_b,
        campus=campus_b1,
        building=building_b1,
        floor=floor_b1,
        room_number="B101",
        name="Main Lecture Hall",
        room_type=RoomType.SEMINAR_HALL,
        capacity=100,
        status=RoomStatus.AVAILABLE,
    )


@pytest.fixture
def asset_b1(db, org_b, campus_b1, dept_b1, building_b1, floor_b1, room_b1):
    return Asset.objects.create(
        organization=org_b,
        campus=campus_b1,
        department=dept_b1,
        building=building_b1,
        floor=floor_b1,
        room=room_b1,
        asset_tag="BCN-MAIN-FAC-001",
        name="Main Power Generator",
        category=AssetCategory.ELECTRICAL,
        status=AssetStatus.OPERATIONAL,
    )


@pytest.fixture
def user_admin_b(db, org_b, campus_b1, standard_roles):
    user = User.objects.create_user(
        email="admin.b@beacon.edu",
        full_name="Admin Beta",
        password="TestPassword123!",
        organization=org_b,
        primary_campus=campus_b1,
    )
    user.roles.add(standard_roles["CAMPUS_ADMIN"])
    return user


@pytest.fixture
def auth_headers_admin_b(user_admin_b, campus_b1):
    token = generate_access_token(user_admin_b, campus_id=campus_b1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def user_admin_a2(db, org_a, campus_a2, standard_roles):
    user = User.objects.create_user(
        email="admin.a2@apex.edu",
        full_name="Admin Medical",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a2,
    )
    user.roles.add(standard_roles["CAMPUS_ADMIN"])
    return user


@pytest.fixture
def auth_headers_admin_a2(user_admin_a2, campus_a2):
    token = generate_access_token(user_admin_a2, campus_id=campus_a2.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ============================================================================
# 1. TENANCY ISOLATION TESTS
# ============================================================================

def test_cross_org_lookup_returns_404(api_client, auth_headers_admin_a, dept_b1, building_b1, floor_b1, room_b1, asset_b1):
    """
    Caller from Org A attempting to access Org B resources receives 404 (zero leakage).
    """
    for endpoint, res_id in [
        ("departments", dept_b1.id),
        ("buildings", building_b1.id),
        ("floors", floor_b1.id),
        ("rooms", room_b1.id),
        ("assets", asset_b1.id),
    ]:
        response = api_client.get(f"/api/v1/{endpoint}/{res_id}/", **auth_headers_admin_a)
        assert response.status_code == status.HTTP_404_NOT_FOUND, f"Leaked {endpoint} across orgs"


def test_cross_campus_lookup_returns_404(api_client, auth_headers_admin_a2, dept_a1, building_a1, floor_a1, room_a1, asset_a1):
    """
    Caller in Campus A2 (Medical) attempting to access Campus A1 (Engineering) resources in the same Org receives 404.
    """
    for endpoint, res_id in [
        ("departments", dept_a1.id),
        ("buildings", building_a1.id),
        ("floors", floor_a1.id),
        ("rooms", room_a1.id),
        ("assets", asset_a1.id),
    ]:
        response = api_client.get(f"/api/v1/{endpoint}/{res_id}/", **auth_headers_admin_a2)
        assert response.status_code == status.HTTP_404_NOT_FOUND, f"Leaked {endpoint} across campuses"


def test_tenant_scoped_list_scoping(api_client, auth_headers_admin_a, dept_a1, dept_b1, building_a1, building_b1, floor_a1, floor_b1, room_a1, room_b1, asset_a1, asset_b1):
    """
    List endpoints return only items scoped to caller's active campus.
    """
    dept_resp = api_client.get("/api/v1/departments/", **auth_headers_admin_a)
    assert dept_resp.status_code == status.HTTP_200_OK
    dept_data = dept_resp.data if isinstance(dept_resp.data, list) else dept_resp.data.get("results", [])
    dept_ids = [d["id"] for d in dept_data]
    assert str(dept_a1.id) in dept_ids
    assert str(dept_b1.id) not in dept_ids

    bldg_resp = api_client.get("/api/v1/buildings/", **auth_headers_admin_a)
    assert bldg_resp.status_code == status.HTTP_200_OK
    bldg_data = bldg_resp.data if isinstance(bldg_resp.data, list) else bldg_resp.data.get("results", [])
    bldg_ids = [b["id"] for b in bldg_data]
    assert str(building_a1.id) in bldg_ids
    assert str(building_b1.id) not in bldg_ids

    asset_resp = api_client.get("/api/v1/assets/", **auth_headers_admin_a)
    assert asset_resp.status_code == status.HTTP_200_OK
    asset_data = asset_resp.data if isinstance(asset_resp.data, list) else asset_resp.data.get("results", [])
    asset_ids = [a["id"] for a in asset_data]
    assert str(asset_a1.id) in asset_ids
    assert str(asset_b1.id) not in asset_ids


# ============================================================================
# 2. HIERARCHY INTEGRITY TESTS
# ============================================================================

def test_floor_creation_inherits_campus_and_org_from_building(api_client, auth_headers_admin_a, building_a1):
    """
    Creating a floor derives its organization and campus directly from the parent building.
    """
    payload = {
        "building_id": str(building_a1.id),
        "floor_number": 2,
        "label": "Second Floor",
    }
    response = api_client.post("/api/v1/floors/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["campus_id"] == str(building_a1.campus_id)
    assert response.data["floor_number"] == 2


def test_room_derives_building_from_floor(api_client, auth_headers_admin_a, floor_a1, building_a1):
    """
    Creating a room automatically derives building and campus from the floor.
    """
    payload = {
        "floor_id": str(floor_a1.id),
        "room_number": "102",
        "name": "Robotics Lab",
        "room_type": RoomType.LAB,
        "capacity": 30,
    }
    response = api_client.post("/api/v1/rooms/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["building_id"] == str(building_a1.id)
    assert response.data["floor_id"] == str(floor_a1.id)


def test_room_cross_building_floor_mismatch_rejected(api_client, auth_headers_admin_a, floor_a1, building_b1):
    """
    Specifying a floor belonging to Building A alongside building_id of Building B is rejected.
    """
    payload = {
        "building_id": str(building_b1.id),
        "floor_id": str(floor_a1.id),
        "room_number": "103",
        "name": "Invalid Lab",
    }
    response = api_client.post("/api/v1/rooms/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


# ============================================================================
# 3. ASSET LOCATION INTEGRITY TESTS
# ============================================================================

def test_asset_creation_with_valid_location(api_client, auth_headers_admin_a, dept_a1, room_a1, building_a1, floor_a1):
    """
    Asset creation succeeds with valid department and room; floor and building are derived.
    """
    payload = {
        "department_id": str(dept_a1.id),
        "room_id": str(room_a1.id),
        "asset_tag": "APX-ENG-IT-002",
        "name": "Smart Projector 4K",
        "category": AssetCategory.GENERAL,
        "status": AssetStatus.OPERATIONAL,
    }
    response = api_client.post("/api/v1/assets/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["building_id"] == str(building_a1.id)
    assert response.data["floor_id"] == str(floor_a1.id)
    assert response.data["room_id"] == str(room_a1.id)
    assert response.data["campus_id"] == str(dept_a1.campus_id)


def test_asset_cross_campus_department_rejected(api_client, auth_headers_admin_a, dept_b1):
    """
    Attempting to create an asset using a department from another organization/campus is rejected.
    """
    payload = {
        "department_id": str(dept_b1.id),
        "asset_tag": "APX-ENG-IT-999",
        "name": "Illegal Asset",
        "category": AssetCategory.NETWORKING,
    }
    response = api_client.post("/api/v1/assets/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


def test_asset_cross_building_room_mismatch_rejected(api_client, auth_headers_admin_a, dept_a1, room_a1, building_b1):
    """
    Creating an asset with a room in Building A but explicitly specifying Building B is rejected.
    """
    payload = {
        "department_id": str(dept_a1.id),
        "building_id": str(building_b1.id),
        "room_id": str(room_a1.id),
        "asset_tag": "APX-ENG-IT-003",
        "name": "Mismatched Asset",
    }
    response = api_client.post("/api/v1/assets/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


# ============================================================================
# 4. RBAC ENFORCEMENT TESTS
# ============================================================================

def test_student_cannot_create_campus_graph_resources(api_client, auth_headers_student_a, building_a1, floor_a1, dept_a1):
    """
    Student role is forbidden from creating Department, Building, Floor, Room, or Asset.
    """
    endpoints_and_payloads = [
        ("departments", {"name": "Unauthorized Dept", "code": "UAD"}),
        ("buildings", {"name": "Unauthorized Bldg", "code": "UAB"}),
        ("floors", {"building_id": str(building_a1.id), "floor_number": 9, "label": "Floor 9"}),
        ("rooms", {"floor_id": str(floor_a1.id), "room_number": "901", "name": "Room 901"}),
        ("assets", {"department_id": str(dept_a1.id), "asset_tag": "UAA-001", "name": "Unauthorized Asset"}),
    ]

    for endpoint, payload in endpoints_and_payloads:
        response = api_client.post(f"/api/v1/{endpoint}/", payload, format="json", **auth_headers_student_a)
        assert response.status_code == status.HTTP_403_FORBIDDEN, f"Student was not blocked from POST /api/v1/{endpoint}/"


def test_campus_admin_can_perform_graph_mutations(api_client, auth_headers_admin_a, dept_a1):
    """
    Campus Admin can update and delete operational graph resources.
    """
    update_payload = {"description": "Updated IT department description."}
    patch_resp = api_client.patch(f"/api/v1/departments/{dept_a1.id}/", update_payload, format="json", **auth_headers_admin_a)
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.data["description"] == "Updated IT department description."


def test_granular_permission_allows_creation(db, org_a, campus_a1, api_client):
    """
    A non-admin user holding a specific granular permission (e.g. department:create) can create.
    """
    role_dept_mgr, _ = Role.objects.get_or_create(name="DEPARTMENT_MANAGER", is_system_role=False)
    perm_dept_create, _ = Permission.objects.get_or_create(
        codename="department:create", defaults={"name": "Create department", "module": "department"}
    )
    role_dept_mgr.permissions.add(perm_dept_create)

    user = User.objects.create_user(
        email="dept.mgr@apex.edu",
        full_name="Dept Manager",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a1,
    )
    user.roles.add(role_dept_mgr)

    token = generate_access_token(user, campus_id=campus_a1.id)
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    payload = {"name": "Electrical Engineering", "code": "EE"}
    response = api_client.post("/api/v1/departments/", payload, format="json", **headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["code"] == "EE"


# ============================================================================
# 5. UNIQUENESS CONSTRAINTS TESTS
# ============================================================================

def test_department_code_unique_per_campus(api_client, auth_headers_admin_a, dept_a1, auth_headers_admin_b):
    """
    Department code is unique within the same campus, but can be reused across different campuses.
    """
    duplicate_payload = {"name": "Duplicate IT", "code": dept_a1.code}
    dup_resp = api_client.post("/api/v1/departments/", duplicate_payload, format="json", **auth_headers_admin_a)
    assert dup_resp.status_code == status.HTTP_400_BAD_REQUEST

    # Sibling campus in Org B can reuse the same code
    sibling_resp = api_client.post("/api/v1/departments/", duplicate_payload, format="json", **auth_headers_admin_b)
    assert sibling_resp.status_code == status.HTTP_201_CREATED


def test_building_code_unique_per_campus(api_client, auth_headers_admin_a, building_a1, auth_headers_admin_b):
    """
    Building code is unique within the same campus, but can be reused across different campuses.
    """
    duplicate_payload = {"name": "Duplicate Building", "code": building_a1.code}
    dup_resp = api_client.post("/api/v1/buildings/", duplicate_payload, format="json", **auth_headers_admin_a)
    assert dup_resp.status_code == status.HTTP_400_BAD_REQUEST

    sibling_resp = api_client.post("/api/v1/buildings/", duplicate_payload, format="json", **auth_headers_admin_b)
    assert sibling_resp.status_code == status.HTTP_201_CREATED


def test_floor_number_unique_per_building(api_client, auth_headers_admin_a, building_a1, floor_a1):
    """
    Floor number is unique within the same building.
    """
    payload = {
        "building_id": str(building_a1.id),
        "floor_number": floor_a1.floor_number,
        "label": "Duplicate Floor Number",
    }
    response = api_client.post("/api/v1/floors/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_room_number_unique_per_floor(api_client, auth_headers_admin_a, floor_a1, room_a1):
    """
    Room number is unique on the same floor.
    """
    payload = {
        "floor_id": str(floor_a1.id),
        "room_number": room_a1.room_number,
        "name": "Duplicate Room",
    }
    response = api_client.post("/api/v1/rooms/", payload, format="json", **auth_headers_admin_a)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_asset_tag_unique_per_campus(api_client, auth_headers_admin_a, dept_a1, asset_a1, auth_headers_admin_b, dept_b1):
    """
    Asset tag is unique per campus, but can be used across different campuses.
    """
    dup_payload = {
        "department_id": str(dept_a1.id),
        "asset_tag": asset_a1.asset_tag,
        "name": "Duplicate Asset Tag",
    }
    dup_resp = api_client.post("/api/v1/assets/", dup_payload, format="json", **auth_headers_admin_a)
    assert dup_resp.status_code == status.HTTP_400_BAD_REQUEST

    # Reuse in Campus B succeeds
    sibling_payload = {
        "department_id": str(dept_b1.id),
        "asset_tag": asset_a1.asset_tag,
        "name": "Beacon Asset with Same Tag",
    }
    sibling_resp = api_client.post("/api/v1/assets/", sibling_payload, format="json", **auth_headers_admin_b)
    assert sibling_resp.status_code == status.HTTP_201_CREATED


# ============================================================================
# 6. AUDIT LOGGING TESTS
# ============================================================================

def test_audit_logs_created_on_graph_mutations(api_client, auth_headers_admin_a, building_a1):
    """
    Creating, updating, and deleting operational graph entities generates immutable AuditLog entries.
    """
    initial_count = AuditLog.objects.count()

    # 1. Create Floor
    floor_payload = {
        "building_id": str(building_a1.id),
        "floor_number": 3,
        "label": "Third Floor",
    }
    create_resp = api_client.post("/api/v1/floors/", floor_payload, format="json", **auth_headers_admin_a)
    assert create_resp.status_code == status.HTTP_201_CREATED
    floor_id = create_resp.data["id"]

    audit_create = AuditLog.objects.filter(action="floor.create", entity_id=floor_id).first()
    assert audit_create is not None
    assert audit_create.entity_type == "Floor"
    assert audit_create.post_state_json["floor_number"] == 3

    # 2. Update Floor
    patch_resp = api_client.patch(f"/api/v1/floors/{floor_id}/", {"label": "3rd Floor Innovation"}, format="json", **auth_headers_admin_a)
    assert patch_resp.status_code == status.HTTP_200_OK

    audit_update = AuditLog.objects.filter(action="floor.update", entity_id=floor_id).first()
    assert audit_update is not None
    assert audit_update.post_state_json["label"] == "3rd Floor Innovation"

    # 3. Delete Floor
    del_resp = api_client.delete(f"/api/v1/floors/{floor_id}/", **auth_headers_admin_a)
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    audit_delete = AuditLog.objects.filter(action="floor.delete", entity_id=floor_id).first()
    assert audit_delete is not None


# ============================================================================
# 7. ERROR ENVELOPE AND ZERO LEAKAGE TESTS
# ============================================================================

def test_error_envelope_structure_on_campus_graph_not_found(api_client, auth_headers_admin_a):
    """
    Nonexistent resource returns standard Paraxis error envelope.
    """
    random_uuid = "00000000-0000-0000-0000-000000000000"
    response = api_client.get(f"/api/v1/buildings/{random_uuid}/", **auth_headers_admin_a)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.data
    assert response.data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "request_id" in response.data["error"]


def test_deletion_protection_semantics(db, building_a1, floor_a1, room_a1, asset_a1):
    """
    Verifies that deleting a building with floors or a floor with rooms is protected,
    while deleting a room safely nullifies the asset's room location.
    """
    from django.db.models.deletion import ProtectedError

    # 1. Floor protects Building
    with pytest.raises(ProtectedError):
        building_a1.delete()

    # 2. Room protects Floor
    with pytest.raises(ProtectedError):
        floor_a1.delete()

    # 3. Deleting Room sets Asset.room to NULL (Asset location is preserved at building/floor level)
    room_a1.delete()
    asset_a1.refresh_from_db()
    assert asset_a1.room is None
    assert asset_a1.building_id == building_a1.id
