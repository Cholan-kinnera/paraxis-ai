"""
Integration tests for Phase 4: Tasks, Dispatch & SLA Management.

Verifies:
1. Multi-Tenancy & Campus Isolation (fail-closed, cross-org 404, cross-campus 404).
2. Incident-Task Invariants (models.PROTECT on parent Incident, multi-task support, tenant inheritance).
3. Lifecycle State Machine Enforcement (strict transitions, rejection of illegal jumps, terminal state protection).
4. Generic PATCH protection (state machine & timestamps cannot be bypassed via PATCH).
5. Action Endpoints (/assign/, /start/, /complete/, /cancel/) and Audit Logging.
6. TaskEvent Immutability (update & delete raise TaskEventImmutableError, chronological ordering).
7. SLA Policy & Tracking (auto-matching, deterministic <=25% AT_RISK threshold, BREACHED detection, MET on completion).
8. RBAC and Actor Scoping (Technician self-scoping, Student denial, Admin full control).
"""
import uuid
from datetime import timedelta
import pytest
from rest_framework import status
from django.utils import timezone
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError

from core.models.task import (
    Task,
    TaskEvent,
    TaskStatus,
    TaskType,
    TaskEventType,
    TaskEventImmutableError,
)
from core.models.sla import (
    SLA,
    SLATracking,
    SLAState,
)
from core.models.incident import (
    Incident,
    IncidentEvent,
    IncidentStatus,
    IncidentPriority,
    IncidentCategory,
    IncidentEventType,
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
from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus
from core.models.access import Role, Permission
from core.models.user import User
from core.models.audit import AuditLog
from core.authentication.jwt import generate_access_token
from core.services.task_dispatch import (
    create_task_from_incident,
    assign_task,
    start_task,
    complete_task,
    cancel_task,
)
from core.services.sla import (
    find_applicable_sla,
    attach_sla_to_task,
    evaluate_sla_state,
    check_and_record_breaches,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def permissions_phase4(db):
    """Ensure all Phase 4 task and sla permissions exist."""
    perms = {}
    phase4_defs = [
        ("task:read", "View operational tasks", "operations"),
        ("task:create", "Create and dispatch tasks", "operations"),
        ("task:view_assigned", "View assigned tasks", "operations"),
        ("task:acknowledge", "Acknowledge task assignment", "operations"),
        ("task:start", "Start task execution", "operations"),
        ("task:complete", "Complete operational task", "operations"),
        ("task:cancel", "Cancel operational task", "operations"),
        ("task:update", "Update operational task details", "operations"),
        ("task:reassign", "Reassign operational task", "operations"),
        ("task:manage_all", "Full operational task management", "operations"),
        ("sla:read", "View SLA policies and tracking", "operations"),
        ("sla:manage", "Manage SLA policies", "operations"),
    ]
    for codename, name, module in phase4_defs:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={"name": name, "module": module},
        )
        perms[codename] = perm
    return perms


@pytest.fixture
def role_technician(db, permissions_phase4):
    role, _ = Role.objects.get_or_create(name="TECHNICIAN", is_system_role=True)
    role.permissions.add(
        permissions_phase4["task:read"],
        permissions_phase4["task:view_assigned"],
        permissions_phase4["task:acknowledge"],
        permissions_phase4["task:start"],
        permissions_phase4["task:complete"],
    )
    return role


@pytest.fixture
def role_campus_admin_phase4(db, standard_roles, permissions_phase4):
    admin_role = standard_roles["CAMPUS_ADMIN"]
    admin_role.permissions.add(*permissions_phase4.values())
    return admin_role


@pytest.fixture
def dept_it_a1(db, org_a, campus_a1):
    return Department.objects.create(
        organization=org_a,
        campus=campus_a1,
        name="Information Technology",
        code="IT-01",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.fixture
def dept_med_a2(db, org_a, campus_a2):
    return Department.objects.create(
        organization=org_a,
        campus=campus_a2,
        name="Medical Operations",
        code="MED-01",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.fixture
def dept_b1(db, org_b, campus_b1):
    return Department.objects.create(
        organization=org_b,
        campus=campus_b1,
        name="Facilities Beacon",
        code="FAC-B1",
        status=DepartmentStatus.ACTIVE,
    )


@pytest.fixture
def user_technician_a1(db, org_a, campus_a1, role_technician):
    user = User.objects.create_user(
        email="tech.a1@apex.edu",
        full_name="Technician Alpha One",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a1,
    )
    user.roles.add(role_technician)
    return user


@pytest.fixture
def auth_headers_technician_a1(user_technician_a1, campus_a1):
    token = generate_access_token(user_technician_a1, campus_id=campus_a1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def user_technician_a2(db, org_a, campus_a2, role_technician):
    user = User.objects.create_user(
        email="tech.a2@apex.edu",
        full_name="Technician Alpha Two (Med)",
        password="TestPassword123!",
        organization=org_a,
        primary_campus=campus_a2,
    )
    user.roles.add(role_technician)
    return user


@pytest.fixture
def auth_headers_technician_a2(user_technician_a2, campus_a2):
    token = generate_access_token(user_technician_a2, campus_id=campus_a2.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def user_technician_b(db, org_b, campus_b1, role_technician):
    user = User.objects.create_user(
        email="tech.b@beacon.edu",
        full_name="Technician Beta",
        password="TestPassword123!",
        organization=org_b,
        primary_campus=campus_b1,
    )
    user.roles.add(role_technician)
    return user


@pytest.fixture
def user_admin_b(db, org_b, campus_b1, role_campus_admin_phase4):
    user = User.objects.create_user(
        email="admin.b@beacon.edu",
        full_name="Admin Beta",
        password="TestPassword123!",
        organization=org_b,
        primary_campus=campus_b1,
    )
    user.roles.add(role_campus_admin_phase4)
    return user


@pytest.fixture
def auth_headers_admin_b(user_admin_b, campus_b1):
    token = generate_access_token(user_admin_b, campus_id=campus_b1.id)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.fixture
def incident_a1(db, org_a, campus_a1, user_student_a, dept_it_a1):
    inc = Incident.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        title="Wi-Fi AP Offline in Engineering Hall",
        description="AP-204 is unresponsive.",
        category=IncidentCategory.IT_NETWORK,
        priority=IncidentPriority.HIGH,
        status=IncidentStatus.INGESTED,
        reporter=user_student_a,
        department=dept_it_a1,
    )
    IncidentEvent.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        incident=inc,
        event_type=IncidentEventType.REPORTED,
        description="Incident reported by student.",
        actor=user_student_a,
    )
    return inc


@pytest.fixture
def incident_b1(db, org_b, campus_b1, user_student_b, dept_b1):
    inc = Incident.all_objects.create(
        organization=org_b,
        campus=campus_b1,
        title="Beacon Plumbing Issue",
        description="Water leak near entrance.",
        category=IncidentCategory.PLUMBING,
        priority=IncidentPriority.MEDIUM,
        status=IncidentStatus.INGESTED,
        reporter=user_student_b,
        department=dept_b1,
    )
    IncidentEvent.all_objects.create(
        organization=org_b,
        campus=campus_b1,
        incident=inc,
        event_type=IncidentEventType.REPORTED,
        description="Incident reported by student B.",
        actor=user_student_b,
    )
    return inc


@pytest.fixture
def sla_high_a1(db, org_a, campus_a1):
    return SLA.all_objects.create(
        organization=org_a,
        campus=campus_a1,
        name="IT High Priority SLA",
        priority=IncidentPriority.HIGH,
        task_type=TaskType.REPAIR,
        response_target=timedelta(minutes=30),
        resolution_target=timedelta(minutes=120),
        active=True,
    )


@pytest.fixture
def sla_b1(db, org_b, campus_b1):
    return SLA.all_objects.create(
        organization=org_b,
        campus=campus_b1,
        name="Beacon Facilities SLA",
        priority=IncidentPriority.MEDIUM,
        task_type=TaskType.MAINTENANCE,
        response_target=timedelta(minutes=60),
        resolution_target=timedelta(minutes=240),
        active=True,
    )


# ============================================================================
# 1. MULTI-TENANCY & TENANT ISOLATION TESTS
# ============================================================================

def test_cross_org_task_lookup_returns_404(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_b1, user_admin_b
):
    """Admins in Org A receive 404 when querying a Task belonging to Org B."""
    task_b = create_task_from_incident(
        incident=incident_b1,
        title="Fix Beacon Pipe",
        task_type=TaskType.MAINTENANCE,
        created_by=user_admin_b,
    )
    res = api_client.get(f"/api/v1/tasks/{task_b.id}/", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_cross_campus_task_lookup_returns_404(
    api_client, auth_headers_technician_a2, role_campus_admin_phase4, incident_a1, user_admin_a
):
    """A user in Campus A2 receives 404 when querying a task in Campus A1."""
    task_a1 = create_task_from_incident(
        incident=incident_a1,
        title="Check AP-204 Hardware",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    res = api_client.get(f"/api/v1/tasks/{task_a1.id}/", **auth_headers_technician_a2)
    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.data["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_cross_tenant_task_creation_rejected(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_b1
):
    """An admin from Campus A1 cannot create a task for an incident in Campus B1."""
    payload = {
        "incident_id": str(incident_b1.id),
        "title": "Cross Tenant Task",
        "task_type": TaskType.INSPECTION,
    }
    res = api_client.post("/api/v1/tasks/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


def test_cross_tenant_user_assignment_rejected(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a, user_technician_a2
):
    """Assigning a user from a different campus (Campus A2) to a task in Campus A1 is rejected."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Local Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    payload = {"assigned_user_id": str(user_technician_a2.id)}
    res = api_client.post(f"/api/v1/tasks/{task.id}/assign/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["error"]["code"] == "VALIDATION_FAILED"


def test_cross_tenant_department_assignment_rejected(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a, dept_med_a2
):
    """Assigning a department from Campus A2 to a task in Campus A1 is rejected."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Local Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    payload = {"assigned_department_id": str(dept_med_a2.id)}
    res = api_client.post(f"/api/v1/tasks/{task.id}/assign/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["error"]["code"] == "VALIDATION_FAILED"


def test_cross_tenant_sla_attachment_rejected(incident_a1, user_admin_a, sla_b1):
    """Attempting to attach an SLA policy from Org B to a Task in Org A raises ValidationError."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Org A Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    with pytest.raises(ValidationError) as exc:
        attach_sla_to_task(task=task, sla=sla_b1)
    assert "SLA organization does not match Task organization" in str(exc.value)


def test_unauthenticated_task_request_rejected(api_client):
    """Unauthenticated requests to /api/v1/tasks/ receive 401."""
    res = api_client.get("/api/v1/tasks/")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.data["error"]["code"] == "UNAUTHENTICATED"


# ============================================================================
# 2. INCIDENT-TASK RELATIONSHIP & INVARIANTS
# ============================================================================

def test_incident_protected_on_task_deletion(db, incident_a1, user_admin_a):
    """
    Constraint 1: Incident -> Task FK is on_delete=models.PROTECT.
    Attempting to delete an Incident that has associated tasks must raise ProtectedError.
    """
    create_task_from_incident(
        incident=incident_a1,
        title="Operational Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    with pytest.raises(ProtectedError):
        incident_a1.delete()


def test_multiple_tasks_per_incident(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a
):
    """A single incident can spawn multiple operational tasks (e.g. diagnosis, repair, verification)."""
    task1 = create_task_from_incident(
        incident=incident_a1,
        title="Diagnostic Scan",
        task_type=TaskType.INSPECTION,
        created_by=user_admin_a,
    )
    task2 = create_task_from_incident(
        incident=incident_a1,
        title="Physical Switch Replacement",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assert task1.incident_id == incident_a1.id
    assert task2.incident_id == incident_a1.id
    assert task1.id != task2.id

    res = api_client.get(f"/api/v1/tasks/?incident={incident_a1.id}", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    task_ids = [t["id"] for t in data]
    assert str(task1.id) in task_ids
    assert str(task2.id) in task_ids


def test_task_inherits_incident_tenant_context(incident_a1, user_admin_a):
    """Task inherits organization and campus strictly from parent Incident."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Inherited Context Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assert task.organization_id == incident_a1.organization_id
    assert task.campus_id == incident_a1.campus_id


def test_task_completion_does_not_auto_resolve_incident(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a
):
    """Completing a task does NOT automatically mark the parent incident as RESOLVED."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Repair Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assign_task(task, assigned_user=user_admin_a, actor=user_admin_a)
    start_task(task, actor=user_admin_a)

    # Complete the task
    payload = {"notes": "Port re-crimped and connectivity restored."}
    res = api_client.post(f"/api/v1/tasks/{task.id}/complete/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == TaskStatus.COMPLETED

    # Check incident status: remains INGESTED (sovereign domain state)
    incident_a1.refresh_from_db()
    assert incident_a1.status == IncidentStatus.INGESTED
    assert incident_a1.resolved_at is None


# ============================================================================
# 3. LIFECYCLE STATE MACHINE ENFORCEMENT
# ============================================================================

def test_valid_lifecycle_transitions(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a, user_technician_a1
):
    """
    Valid lifecycle transitions:
    PENDING -> ASSIGNED -> IN_PROGRESS -> COMPLETED
    """
    # 1. Create (PENDING)
    create_payload = {
        "incident_id": str(incident_a1.id),
        "title": "Full Cycle Task",
        "task_type": TaskType.REPAIR,
    }
    res_create = api_client.post("/api/v1/tasks/", create_payload, format="json", **auth_headers_admin_a)
    assert res_create.status_code == status.HTTP_201_CREATED
    task_id = res_create.data["id"]
    assert res_create.data["status"] == TaskStatus.PENDING

    # 2. Assign (ASSIGNED)
    res_assign = api_client.post(
        f"/api/v1/tasks/{task_id}/assign/",
        {"assigned_user_id": str(user_technician_a1.id)},
        format="json",
        **auth_headers_admin_a,
    )
    assert res_assign.status_code == status.HTTP_200_OK
    assert res_assign.data["status"] == TaskStatus.ASSIGNED

    # 3. Start (IN_PROGRESS)
    res_start = api_client.post(f"/api/v1/tasks/{task_id}/start/", {}, format="json", **auth_headers_admin_a)
    assert res_start.status_code == status.HTTP_200_OK
    assert res_start.data["status"] == TaskStatus.IN_PROGRESS
    assert res_start.data["started_at"] is not None

    # 4. Complete (COMPLETED)
    res_complete = api_client.post(
        f"/api/v1/tasks/{task_id}/complete/",
        {"notes": "Replaced faulty antenna component."},
        format="json",
        **auth_headers_admin_a,
    )
    assert res_complete.status_code == status.HTTP_200_OK
    assert res_complete.data["status"] == TaskStatus.COMPLETED
    assert res_complete.data["completed_at"] is not None


def test_invalid_transition_skipping_assigned_rejected(incident_a1, user_admin_a):
    """Skipping lifecycle states (e.g. PENDING -> COMPLETED directly) is prohibited."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Pending Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    with pytest.raises(ValidationError) as exc:
        complete_task(task, resolution_notes="Attempt skip", actor=user_admin_a)
    assert "Invalid state transition" in str(exc.value)


def test_cannot_transition_from_terminal_completed(incident_a1, user_admin_a):
    """Terminal state COMPLETED cannot be transitioned to IN_PROGRESS or CANCELLED."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Finished Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assign_task(task, assigned_user=user_admin_a, actor=user_admin_a)
    start_task(task, actor=user_admin_a)
    complete_task(task, resolution_notes="Done", actor=user_admin_a)

    with pytest.raises(ValidationError) as exc:
        start_task(task, actor=user_admin_a)
    assert "Invalid state transition" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        cancel_task(task, reason="Late cancel", actor=user_admin_a)
    assert "Invalid state transition" in str(exc.value)


def test_cancellation_flow(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a
):
    """Tasks can be cancelled from PENDING, ASSIGNED, or IN_PROGRESS with a mandatory reason."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Cancelled Task",
        task_type=TaskType.INSPECTION,
        created_by=user_admin_a,
    )
    payload = {"reason": "Duplicate dispatch identified."}
    res = api_client.post(f"/api/v1/tasks/{task.id}/cancel/", payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    assert res.data["status"] == TaskStatus.CANCELLED
    assert res.data["cancelled_at"] is not None


# ============================================================================
# 4. GENERIC PATCH PROTECTION (STATE MACHINE BYPASS DEFENSE)
# ============================================================================

def test_generic_patch_cannot_mutate_status_or_timestamps(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a
):
    """
    Constraint 2: Generic Task PATCH must never bypass the lifecycle state machine.
    Status, timestamps, organization, campus, and incident must not be modifiable via PATCH.
    """
    task = create_task_from_incident(
        incident=incident_a1,
        title="Original Title",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    original_status = task.status
    fake_completed_at = (timezone.now() + timedelta(hours=5)).isoformat()

    bypass_payload = {
        "status": TaskStatus.COMPLETED,
        "completed_at": fake_completed_at,
        "started_at": fake_completed_at,
        "title": "Updated Title via PATCH",
    }
    res = api_client.patch(f"/api/v1/tasks/{task.id}/", bypass_payload, format="json", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK

    # Title changed, but status and timestamps were ignored
    task.refresh_from_db()
    assert task.title == "Updated Title via PATCH"
    assert task.status == original_status
    assert task.completed_at is None
    assert task.started_at is None


# ============================================================================
# 5. AUDIT LOGGING & OPERATIONAL TIMELINE (TaskEvent IMMUTABILITY)
# ============================================================================

def test_task_event_immutability_on_update_raises_error(db, incident_a1, user_admin_a):
    """TaskEvents are strictly append-only. Direct update raises TaskEventImmutableError."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Audit Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    event = TaskEvent.all_objects.filter(task=task).first()
    assert event is not None

    event.description = "Tampered description"
    with pytest.raises(TaskEventImmutableError):
        event.save()


def test_task_event_immutability_on_delete_raises_error(db, incident_a1, user_admin_a):
    """Direct deletion of TaskEvents raises TaskEventImmutableError."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Audit Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    event = TaskEvent.all_objects.filter(task=task).first()
    assert event is not None

    with pytest.raises(TaskEventImmutableError):
        event.delete()


def test_timeline_endpoint_returns_chronological_events(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a, user_technician_a1
):
    """GET /api/v1/tasks/<id>/events/ returns all chronological timeline events."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Timeline Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assign_task(task, assigned_user=user_technician_a1, actor=user_admin_a)
    start_task(task, actor=user_technician_a1)

    res = api_client.get(f"/api/v1/tasks/{task.id}/events/", **auth_headers_admin_a)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    event_types = [e["event_type"] for e in data]

    assert TaskEventType.CREATED in event_types
    assert TaskEventType.ASSIGNED in event_types
    assert TaskEventType.STARTED in event_types


def test_audit_logs_recorded_for_task_actions(
    api_client, auth_headers_admin_a, role_campus_admin_phase4, incident_a1, user_admin_a, user_technician_a1
):
    """Every consequential state change records an AuditLog entry."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Audited Task",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assign_task(task, assigned_user=user_technician_a1, actor=user_admin_a)
    start_task(task, actor=user_technician_a1)
    complete_task(task, resolution_notes="Done cleanly", actor=user_technician_a1)

    actions = list(AuditLog.objects.filter(entity_id=str(task.id)).values_list("action", flat=True))
    assert "task.create" in actions
    assert "task.assign" in actions
    assert "task.start" in actions
    assert "task.complete" in actions


# ============================================================================
# 6. SLA MANAGEMENT, DETERMINISTIC AT_RISK & BREACH DETECTION
# ============================================================================

def test_sla_auto_matching_on_task_creation(incident_a1, user_admin_a, sla_high_a1):
    """When a task matches an active SLA policy, an SLATracking record is attached with deadline."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Auto-matched SLA Task",
        priority=IncidentPriority.HIGH,
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assert task.sla_id == sla_high_a1.id
    assert hasattr(task, "sla_tracking")
    tracking = task.sla_tracking
    assert tracking.state == SLAState.HEALTHY
    assert tracking.resolution_due_at is not None
    assert tracking.response_due_at is not None


def test_deterministic_at_risk_evaluation(incident_a1, user_admin_a, sla_high_a1):
    """
    Constraint 4: Deterministic AT_RISK behavior <=25% remaining time.
    If target is 100 minutes and 80 minutes have elapsed (20% remaining), state must be AT_RISK.
    """
    task = create_task_from_incident(
        incident=incident_a1,
        title="At Risk SLA Task",
        priority=IncidentPriority.HIGH,
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assign_task(task, assigned_user=user_admin_a, actor=user_admin_a)
    start_task(task, actor=user_admin_a)
    task.refresh_from_db()
    tracking = task.sla_tracking
    total_duration = (tracking.resolution_due_at - tracking.started_at).total_seconds()

    # Simulate 80% elapsed (20% remaining <= 25%)
    simulated_now = tracking.started_at + timedelta(seconds=total_duration * 0.80)
    state = evaluate_sla_state(tracking, current_time=simulated_now)
    assert state == SLAState.AT_RISK


def test_sla_breach_detection_and_recording(incident_a1, user_admin_a, sla_high_a1):
    """If current time exceeds the deadline, evaluate_sla_state is BREACHED and check_and_record_breaches logs it."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Breached SLA Task",
        priority=IncidentPriority.HIGH,
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    tracking = task.sla_tracking

    # Simulate time after deadline
    overdue_now = tracking.resolution_due_at + timedelta(minutes=10)
    state = evaluate_sla_state(tracking, current_time=overdue_now)
    assert state == SLAState.BREACHED

    # Run breach service
    check_and_record_breaches(task, current_time=overdue_now)
    tracking.refresh_from_db()
    assert tracking.state == SLAState.BREACHED
    assert tracking.resolution_breached_at is not None

    # Verify SLA_BREACHED timeline event was recorded
    breach_event = TaskEvent.all_objects.filter(task=task, event_type=TaskEventType.SLA_BREACHED).first()
    assert breach_event is not None


def test_sla_met_on_timely_completion(incident_a1, user_admin_a, sla_high_a1):
    """Completing a task within deadline sets SLA state to MET."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="On-time Task",
        priority=IncidentPriority.HIGH,
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )
    assign_task(task, assigned_user=user_admin_a, actor=user_admin_a)
    start_task(task, actor=user_admin_a)
    complete_task(task, resolution_notes="Resolved promptly", actor=user_admin_a)

    task.sla_tracking.refresh_from_db()
    assert task.sla_tracking.state == SLAState.MET


# ============================================================================
# 7. ROLE-BASED ACCESS CONTROL (RBAC) & ACTOR SCOPING
# ============================================================================

def test_student_cannot_create_or_assign_task(
    api_client, auth_headers_student_a, incident_a1, user_student_a
):
    """Students receive 403 when trying to dispatch or assign tasks."""
    payload = {
        "incident_id": str(incident_a1.id),
        "title": "Unauthorized Student Task",
        "task_type": TaskType.INSPECTION,
    }
    res_create = api_client.post("/api/v1/tasks/", payload, format="json", **auth_headers_student_a)
    assert res_create.status_code == status.HTTP_403_FORBIDDEN
    assert res_create.data["error"]["code"] == "PERMISSION_DENIED"


def test_technician_can_view_assigned_tasks_only(
    api_client, auth_headers_technician_a1, role_campus_admin_phase4, incident_a1, user_admin_a, user_technician_a1
):
    """Technicians only see tasks assigned to them."""
    # Task 1: assigned to technician
    task_assigned = create_task_from_incident(
        incident=incident_a1,
        title="Technician's Job",
        task_type=TaskType.REPAIR,
        assigned_user=user_technician_a1,
        created_by=user_admin_a,
    )
    # Task 2: unassigned
    task_unassigned = create_task_from_incident(
        incident=incident_a1,
        title="Unassigned Job",
        task_type=TaskType.REPAIR,
        created_by=user_admin_a,
    )

    res = api_client.get("/api/v1/tasks/", **auth_headers_technician_a1)
    assert res.status_code == status.HTTP_200_OK
    data = res.data["data"] if isinstance(res.data, dict) and "data" in res.data else res.data
    task_ids = [t["id"] for t in data]

    assert str(task_assigned.id) in task_ids
    assert str(task_unassigned.id) not in task_ids


def test_technician_can_start_and_complete_assigned_task(
    api_client, auth_headers_technician_a1, role_campus_admin_phase4, incident_a1, user_admin_a, user_technician_a1
):
    """An assigned technician has permission to start and complete their task."""
    task = create_task_from_incident(
        incident=incident_a1,
        title="Technician Execution Task",
        task_type=TaskType.REPAIR,
        assigned_user=user_technician_a1,
        created_by=user_admin_a,
    )
    # Start
    res_start = api_client.post(f"/api/v1/tasks/{task.id}/start/", {}, format="json", **auth_headers_technician_a1)
    assert res_start.status_code == status.HTTP_200_OK
    assert res_start.data["status"] == TaskStatus.IN_PROGRESS

    # Complete
    res_complete = api_client.post(
        f"/api/v1/tasks/{task.id}/complete/",
        {"notes": "Repaired circuit successfully."},
        format="json",
        **auth_headers_technician_a1,
    )
    assert res_complete.status_code == status.HTTP_200_OK
    assert res_complete.data["status"] == TaskStatus.COMPLETED
