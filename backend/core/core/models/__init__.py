"""
Canonical domain models for Paraxis AI Core Platform.
"""
from core.models.base import TimeStampedModel, TenantScopedModel, TenantScopedManager
from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus
from core.models.access import Permission, Role
from core.models.user import User, UserManager
from core.models.audit import AuditLog, ActorType, AuditLogImmutableError
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
from core.models.sla import (
    SLA,
    SLATracking,
    SLAState,
)
from core.models.task import (
    Task,
    TaskEvent,
    TaskStatus,
    TaskType,
    TaskEventType,
    TaskEventImmutableError,
    VALID_TASK_TRANSITIONS,
)

__all__ = [
    "TimeStampedModel",
    "TenantScopedModel",
    "TenantScopedManager",
    "Organization",
    "Campus",
    "OrganizationStatus",
    "CampusStatus",
    "Permission",
    "Role",
    "User",
    "UserManager",
    "AuditLog",
    "ActorType",
    "AuditLogImmutableError",
    "Department",
    "Building",
    "Floor",
    "Room",
    "Asset",
    "DepartmentStatus",
    "BuildingStatus",
    "RoomType",
    "RoomStatus",
    "AssetCategory",
    "AssetStatus",
    "Incident",
    "IncidentEvent",
    "IncidentStatus",
    "IncidentPriority",
    "IncidentCategory",
    "IncidentSource",
    "IncidentEventType",
    "IncidentEventImmutableError",
    "SLA",
    "SLATracking",
    "SLAState",
    "Task",
    "TaskEvent",
    "TaskStatus",
    "TaskType",
    "TaskEventType",
    "TaskEventImmutableError",
    "VALID_TASK_TRANSITIONS",
]
