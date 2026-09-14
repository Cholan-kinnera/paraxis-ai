"""
Integration tests for Phase 3: Incident & Issue Management.
Verifies:
- Tenancy isolation (cross-org 404, cross-campus 404, fail-closed without context)
- Location hierarchy integrity and automatic graph derivation
- Lifecycle state transitions and validation
- Role-Based Access Control (Student self-scoping, admin authority, mutation guards)
- Operational timeline (IncidentEvent immutability and chronological history)
- Comprehensive audit logging for all mutations
- Historical record protection and soft deletion
- API error envelope compliance
"""
import uuid
import pytest
from rest_framework import status
from django.utils import timezone

from core.models.incident import (
    Incident,
    IncidentEvent,
    IncidentStatus,
    IncidentPriority,
    IncidentCategory,
    IncidentSource,
    IncidentEventType,
    IncidentEventImmutableError,
)
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
def building_a2(db, org_a, campus_a2):
    """Building in Campus A2 (Medical Campus) within same Organization A."""
    return Building.objects.create(
        organization=org_a,
        campus=campus_a2,
        name="Medical Research Complex",
        code="MRC",
        floors_count=6,
        status=BuildingStatus.OPERATIONAL,
    )


@pytest.fixture
def dept_a2(db, org_a, campus_a2):
    """Department in Campus A2 (Medical Campus)."""
    return Department.objects.create(
        organization=org_a,
        campus=campus_a2,
        name="Medical Diagnostics",
        code="DIAG",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.fixture
def user_student_a2(db, org_a, campus_a1, standard_roles):
    """A second student in the same campus (Campus A1) to verify self-scoping."""
    user = User.objects.create_user(
        email="student.a2@apex.edu",
        full_name="Student Alpha Two",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a1,
    )
    user.roles.add(standard_roles["STUDENT"])
    return user


@pytest.fixture
def auth_headers_student_a2(user_student_a2, campus_a1):
    token = generate_access_token(user_student_a2, campus_id=campus_a1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def user_guest_no_perms(db, org_a, campus_a1):
    """A user in Org A / Campus A1 with no permissions or roles."""
    return User.objects.create_user(
        email="guest.user@apex.edu",
        full_name="Guest User",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a1,
    )


@pytest.fixture
def auth_headers_guest(user_guest_no_perms, campus_a1):
    token = generate_access_token(user_guest_no_perms, campus_id=campus_a1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def incident_a1(db, org_a, campus_a1, user_student_a, dept_a1, building_a1, floor_a1, room_a1, asset_a1):
    inc = Incident.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        title="Wi-Fi AP Unresponsive in Lab 101",
        description="The access point is completely offline and blinking amber.",
        category=IncidentCategory.IT_NETWORK,
        priority=IncidentPriority.HIGH,
        status=IncidentStatus.INGESTED,
        reporter=user_student_a,
        department=dept_a1,
        building=building_a1,
        floor=floor_a1,
        room=room_a1,
        asset=asset_a1,
    )
    IncidentEvent.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        incident=inc,
        event_type=IncidentEventType.REPORTED,
        description="Incident reported by Student Alpha.",
        actor=user_student_a,
    )
    return inc


@pytest.fixture
def incident_b1(db, org_b, campus_b1, user_student_b):
    inc = Incident.all_objects.create(
        organization=org_b,
        campus=campus_b1,
        title="Water leak in Beacon Main Hall",
        description="Pipes leaking under main entrance.",
        category=IncidentCategory.PLUMBING,
        priority=IncidentPriority.MEDIUM,
        status=IncidentStatus.INGESTED,
        reporter=user_student_b,
    )
    IncidentEvent.all_objects.create(
        organization=org_b,
        campus=campus_b1,
        incident=inc,
        event_type=IncidentEventType.REPORTED,
        description="Incident reported by Student Beta.",
        actor=user_student_b,
    )
    return inc


# ============================================================================
# 1. TENANCY ISOLATION TESTS
# ============================================================================

def test_cross_org_incident_lookup_returns_404(api_client, auth_headers_admin_a, incident_b1):
    """Admins in Organization A must receive 404 when querying an incident in Organization B."""
    url = f"/api/v1/incidents/{incident_b1.id}/"
    res = api_client.get(url, **auth_headers_admin_a)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_cross_campus_incident_lookup_returns_404(api_client, org_a, campus_a2, user_student_a, incident_a1):
    """A user in Campus A2 receives 404 when querying an incident in Campus A1."""
    user_campus_a2 = User.objects.create_user(
        email="student.med@apex.edu",
        full_name="Med Student",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a2,
    )
    token = generate_access_token(user_campus_a2, campus_id=campus_a2.id)
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    url = f"/api/v1/incidents/{incident_a1.id}/"
    res = api_client.get(url, **headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_incident_list_scoped_to_active_campus(api_client, auth_headers_admin_a, incident_a1, incident_b1):
    """Listing incidents returns only incidents from the caller's active campus."""
    res = api_client.get("/api/v1/incidents/", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    incident_ids = [item["id"] for item in data]
    assert str(incident_a1.id) in incident_ids
    assert str(incident_b1.id) not in incident_ids


def test_unauthenticated_request_rejected(api_client):
    """Unauthenticated requests receive 401 Unauthorized with standard error envelope."""
    res = api_client.get("/api/v1/incidents/")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data["error"]["code"] == "UNAUTHENTICATED"


# ============================================================================
# 2. CREATION & GRAPH DERIVATION TESTS
# ============================================================================

def test_valid_incident_creation_by_student_with_room(api_client, auth_headers_student_a, user_student_a, room_a1, building_a1, floor_a1):
    """
    When a student submits an incident with room_id:
    - Reporter is automatically assigned to the authenticated student
    - Building and floor are automatically derived from the room
    - Status defaults to INGESTED
    - A REPORTED timeline event is created
    - An AuditLog incident.create event is created
    """
    payload = {
        "title": "Projector not displaying HDMI signal",
        "description": "The overhead projector in room 101 does not respond to the podium cable.",
        "category": IncidentCategory.IT_NETWORK,
        "room_id": str(room_a1.id),
    }
    res = api_client.post("/api/v1/incidents/", payload, format="json", **auth_headers_student_a)
    assert res.status_code == status.HTTP_201_CREATED

    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    assert data["title"] == payload["title"]
    assert data["status"] == IncidentStatus.INGESTED
    assert data["reporter_id"] == str(user_student_a.id)
    assert data["reporter_email"] == user_student_a.email

    # Verify automatic location derivation
    assert data["room_id"] == str(room_a1.id)
    assert data["floor_id"] == str(floor_a1.id)
    assert data["building_id"] == str(building_a1.id)
    assert data["building_code"] == building_a1.code

    # Verify timeline event
    incident_id = data["id"]
    timeline_event = IncidentEvent.all_objects.filter(incident_id=incident_id, event_type=IncidentEventType.REPORTED).first()
    assert timeline_event is not None
    assert timeline_event.actor == user_student_a

    # Verify audit log
    audit_entry = AuditLog.objects.filter(entity_type="Incident", entity_id=incident_id, action="incident.create").first()
    assert audit_entry is not None
    assert audit_entry.actor == user_student_a


def test_asset_auto_derives_room_floor_and_building(api_client, auth_headers_admin_a, asset_a1, room_a1, floor_a1, building_a1):
    """
    Submitting an incident with only asset_id automatically derives room, floor, and building.
    """
    payload = {
        "title": "Switch fan failure alarm active",
        "description": "Core switch is alarming on auxiliary power supply fan.",
        "category": IncidentCategory.IT_NETWORK,
        "priority": IncidentPriority.HIGH,
        "asset_id": str(asset_a1.id),
    }
    res = api_client.post("/api/v1/incidents/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_201_CREATED

    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    assert data["asset_id"] == str(asset_a1.id)
    assert data["room_id"] == str(room_a1.id)
    assert data["floor_id"] == str(floor_a1.id)
    assert data["building_id"] == str(building_a1.id)


# ============================================================================
# 3. LOCATION INTEGRITY TESTS
# ============================================================================

def test_cross_campus_building_rejected(api_client, auth_headers_admin_a, building_a2):
    """Referencing a building from another campus is rejected with 400 Bad Request."""
    payload = {
        "title": "Roof leak in Medical Building",
        "description": "Reported from Engineering token but references Medical building.",
        "category": IncidentCategory.FACILITY,
        "building_id": str(building_a2.id),
    }
    res = api_client.post("/api/v1/incidents/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "building_id" in str(res.data)


def test_cross_campus_asset_rejected(api_client, auth_headers_admin_a, org_a, campus_a2, building_a2, dept_a2):
    """Referencing an asset from another campus is rejected."""
    asset_med = Asset.objects.create(
        organization=org_a,
        campus=campus_a2,
        department=dept_a2,
        building=building_a2,
        asset_tag="MED-SCANNER-001",
        name="MRI Scanner Unit",
        category=AssetCategory.ELECTRICAL,
        status=AssetStatus.OPERATIONAL,
    )
    payload = {
        "title": "Scanner calibration error",
        "description": "Attempting to report scanner on Engineering campus.",
        "category": IncidentCategory.ELECTRICAL,
        "asset_id": str(asset_med.id),
    }
    res = api_client.post("/api/v1/incidents/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "asset_id" in str(res.data)


def test_asset_and_building_mismatch_rejected(api_client, auth_headers_admin_a, asset_a1, org_a, campus_a1):
    """Providing both asset_id and a building_id that does not match asset's building is rejected."""
    another_building = Building.objects.create(
        organization=org_a,
        campus=campus_a1,
        name="Mechanical Block C",
        code="MBC",
        floors_count=3,
        status=BuildingStatus.OPERATIONAL,
    )
    payload = {
        "title": "Switch issue with wrong building",
        "description": "Switch APX-ENG-IT-001 is in SEB, but caller specified MBC.",
        "category": IncidentCategory.IT_NETWORK,
        "asset_id": str(asset_a1.id),
        "building_id": str(another_building.id),
    }
    res = api_client.post("/api/v1/incidents/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "building_id" in str(res.data)


# ============================================================================
# 4. LIFECYCLE & STATE MACHINE TESTS
# ============================================================================

def test_valid_lifecycle_transitions(api_client, auth_headers_admin_a, incident_a1, user_admin_a):
    """
    Verifies valid progression through the canonical operational state machine:
    INGESTED -> TRIAGING -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> VERIFIED -> CLOSED
    """
    url = f"/api/v1/incidents/{incident_a1.id}/"

    steps = [
        (IncidentStatus.TRIAGING, {}),
        (IncidentStatus.ASSIGNED, {"assigned_to_id": str(user_admin_a.id)}),
        (IncidentStatus.IN_PROGRESS, {}),
        (IncidentStatus.RESOLVED, {"resolution_notes": "Firmware rebooted, Wi-Fi operational."}),
        (IncidentStatus.VERIFIED, {}),
        (IncidentStatus.CLOSED, {}),
    ]

    for next_status, extra_fields in steps:
        payload = {"status": next_status, **extra_fields}
        res = api_client.patch(url, payload, format="json", **auth_headers_admin_a)
        assert res.status_code == status.HTTP_200_OK, f"Failed transitioning to {next_status}: {res.data}"
        data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
        assert data["status"] == next_status

    # Verify RESOLVED set resolved_at timestamp
    incident_a1.refresh_from_db()
    assert incident_a1.resolved_at is not None
    assert incident_a1.resolution_notes == "Firmware rebooted, Wi-Fi operational."


def test_invalid_lifecycle_transition_rejected(api_client, auth_headers_admin_a, incident_a1):
    """Directly skipping states (e.g., INGESTED -> CLOSED) is prohibited by the state machine."""
    url = f"/api/v1/incidents/{incident_a1.id}/"
    res = api_client.patch(url, {"status": IncidentStatus.CLOSED}, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "status" in str(res.data)


def test_status_transition_records_timeline_event_and_audit(api_client, auth_headers_admin_a, incident_a1, user_admin_a):
    """Status changes generate typed IncidentEvents and audit logs."""
    url = f"/api/v1/incidents/{incident_a1.id}/"
    res = api_client.patch(url, {"status": IncidentStatus.TRIAGING}, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK

    # Timeline event
    event = IncidentEvent.all_objects.filter(
        incident=incident_a1,
        event_type=IncidentEventType.STATUS_CHANGED,
    ).first()
    assert event is not None
    assert event.metadata["from_status"] == IncidentStatus.INGESTED
    assert event.metadata["to_status"] == IncidentStatus.TRIAGING

    # Audit log
    audit = AuditLog.objects.filter(
        entity_type="Incident",
        entity_id=str(incident_a1.id),
        action="incident.update",
    ).first()
    assert audit is not None
    assert audit.actor == user_admin_a


# ============================================================================
# 5. RBAC & PERMISSION BOUNDARIES
# ============================================================================

def test_student_sees_only_own_reported_incidents(api_client, auth_headers_student_a, auth_headers_student_a2, user_student_a2, org_a, campus_a1, incident_a1):
    """
    Student A reports Incident A1.
    Student A2 reports Incident A2.
    Student A list query only returns Incident A1.
    """
    incident_a2 = Incident.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        title="Classroom light out",
        description="Flickering light in hall.",
        category=IncidentCategory.ELECTRICAL,
        priority=IncidentPriority.LOW,
        status=IncidentStatus.INGESTED,
        reporter=user_student_a2,
    )

    # Student A queries list
    res_a = api_client.get("/api/v1/incidents/", **auth_headers_student_a)
    assert res_a.status_code == status.HTTP_200_OK
    data_a = res_a.data["data"] if isinstance(res_a.data, dict) and "data" in res_a.data else res_a.data
    ids_a = [item["id"] for item in data_a]
    assert str(incident_a1.id) in ids_a
    assert str(incident_a2.id) not in ids_a

    # Student A2 queries list
    res_a2 = api_client.get("/api/v1/incidents/", **auth_headers_student_a2)
    assert res_a2.status_code == status.HTTP_200_OK
    data_a2 = res_a2.data["data"] if isinstance(res_a2.data, dict) and "data" in res_a2.data else res_a2.data
    ids_a2 = [item["id"] for item in data_a2]
    assert str(incident_a2.id) in ids_a2
    assert str(incident_a1.id) not in ids_a2


def test_student_cannot_view_another_student_incident_detail(api_client, auth_headers_student_a, user_student_a2, org_a, campus_a1):
    """Student A attempting to access Student A2's incident detail receives 404."""
    incident_a2 = Incident.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        title="Private safety concern",
        description="Confidential incident report.",
        category=IncidentCategory.SAFETY,
        priority=IncidentPriority.MEDIUM,
        status=IncidentStatus.INGESTED,
        reporter=user_student_a2,
    )

    url = f"/api/v1/incidents/{incident_a2.id}/"
    res = api_client.get(url, **auth_headers_student_a)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_user_without_incident_create_permission_cannot_create(api_client, auth_headers_guest):
    """A user lacking incident:create permission receives 403 Forbidden."""
    payload = {
        "title": "Unauthorized incident",
        "description": "Should be rejected.",
        "category": IncidentCategory.OTHER,
    }
    res = api_client.post("/api/v1/incidents/", payload, format="json", **auth_headers_guest)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.data["error"]["code"] == "PERMISSION_DENIED"


def test_student_cannot_modify_administrative_fields(api_client, auth_headers_student_a, incident_a1, user_admin_a):
    """Students cannot modify administrative fields (e.g., assigning a staff member or elevating priority)."""
    url = f"/api/v1/incidents/{incident_a1.id}/"
    payload = {"assigned_to_id": str(user_admin_a.id)}
    res = api_client.patch(url, payload, format="json", **auth_headers_student_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "assigned_to_id" in str(res.data)


def test_student_can_confirm_resolution(api_client, auth_headers_admin_a, auth_headers_student_a, incident_a1):
    """When an incident is RESOLVED, the student reporter can verify or reopen it."""
    # Directly set to RESOLVED in database
    Incident.all_objects.filter(id=incident_a1.id).update(status=IncidentStatus.RESOLVED)

    url = f"/api/v1/incidents/{incident_a1.id}/"

    # Student confirms resolution -> VERIFIED
    res = api_client.patch(url, {"status": IncidentStatus.VERIFIED}, format="json", **auth_headers_student_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    assert data["status"] == IncidentStatus.VERIFIED


def test_student_cannot_delete_incident(api_client, auth_headers_student_a, incident_a1):
    """Students cannot delete incidents (receives 403 Forbidden)."""
    url = f"/api/v1/incidents/{incident_a1.id}/"
    res = api_client.delete(url, **auth_headers_student_a)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_campus_admin_can_soft_delete_incident(api_client, auth_headers_admin_a, incident_a1, user_admin_a):
    """Campus Admin can soft-delete an incident, which logs an audit record and removes it from normal views."""
    url = f"/api/v1/incidents/{incident_a1.id}/"
    res = api_client.delete(url, **auth_headers_admin_a)
    assert res.status_code == status.HTTP_204_NO_CONTENT

    # Verify soft deleted in database
    incident_a1.refresh_from_db()
    assert incident_a1.deleted_at is not None

    # Subsequent GET returns 404
    res_get = api_client.get(url, **auth_headers_admin_a)
    assert res_get.status_code == status.HTTP_404_NOT_FOUND

    # Verify audit log
    audit = AuditLog.objects.filter(
        entity_type="Incident",
        entity_id=str(incident_a1.id),
        action="incident.delete",
    ).first()
    assert audit is not None
    assert audit.actor == user_admin_a


# ============================================================================
# 6. OPERATIONAL TIMELINE & IMMUTABILITY TESTS
# ============================================================================

def test_get_incident_timeline_events(api_client, auth_headers_admin_a, incident_a1):
    """GET /api/v1/incidents/<id>/events/ returns chronological operational timeline."""
    url = f"/api/v1/incidents/{incident_a1.id}/events/"
    res = api_client.get(url, **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK

    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    assert len(data) >= 1
    assert data[0]["event_type"] == IncidentEventType.REPORTED


def test_cross_tenant_timeline_returns_404(api_client, auth_headers_student_b, incident_a1):
    """User in Organization B querying Organization A incident timeline receives 404."""
    url = f"/api/v1/incidents/{incident_a1.id}/events/"
    res = api_client.get(url, **auth_headers_student_b)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_incident_event_is_immutable(incident_a1):
    """IncidentEvent records cannot be updated or deleted directly via ORM."""
    event = IncidentEvent.all_objects.filter(incident=incident_a1).first()
    assert event is not None

    with pytest.raises(IncidentEventImmutableError):
        event.description = "Tampered description"
        event.save()

    with pytest.raises(IncidentEventImmutableError):
        event.delete()


# ============================================================================
# 7. FILTERING & SEARCH TESTS
# ============================================================================

def test_filtering_by_status_and_priority(api_client, auth_headers_admin_a, incident_a1, org_a, campus_a1, user_student_a):
    """Query parameter filtering by status and priority works correctly."""
    # Create an additional incident with different status/priority
    Incident.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        title="Cafeteria coffee maker issue",
        description="Descaling required.",
        category=IncidentCategory.FACILITY,
        priority=IncidentPriority.LOW,
        status=IncidentStatus.RESOLVED,
        reporter=user_student_a,
    )

    # Filter by status=INGESTED
    res = api_client.get("/api/v1/incidents/?status=INGESTED", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    assert all(item["status"] == IncidentStatus.INGESTED for item in data)

    # Filter by priority=HIGH
    res = api_client.get("/api/v1/incidents/?priority=HIGH", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    assert all(item["priority"] == IncidentPriority.HIGH for item in data)
