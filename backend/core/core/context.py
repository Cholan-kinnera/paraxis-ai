"""
Tenant and request context abstraction for Paraxis AI.
Uses Python contextvars for safe isolation across async/threaded request lifecycles.
"""
from contextvars import ContextVar
from typing import Optional
import uuid

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_organization_id: ContextVar[Optional[uuid.UUID]] = ContextVar("organization_id", default=None)
_campus_id: ContextVar[Optional[uuid.UUID]] = ContextVar("campus_id", default=None)
_actor_id: ContextVar[Optional[uuid.UUID]] = ContextVar("actor_id", default=None)


def set_current_request_id(request_id: Optional[str]) -> None:
    _request_id.set(request_id)


def get_current_request_id() -> Optional[str]:
    return _request_id.get()


def set_current_trace_id(trace_id: Optional[str]) -> None:
    _trace_id.set(trace_id)


def get_current_trace_id() -> Optional[str]:
    return _trace_id.get()


def set_current_actor_id(actor_id: Optional[uuid.UUID]) -> None:
    if isinstance(actor_id, str):
        actor_id = uuid.UUID(actor_id)
    _actor_id.set(actor_id)


def get_current_actor_id() -> Optional[uuid.UUID]:
    return _actor_id.get()


def set_current_tenant(organization_id: Optional[uuid.UUID], campus_id: Optional[uuid.UUID] = None) -> None:
    if isinstance(organization_id, str):
        organization_id = uuid.UUID(organization_id)
    if isinstance(campus_id, str):
        campus_id = uuid.UUID(campus_id)
    _organization_id.set(organization_id)
    _campus_id.set(campus_id)


def get_current_organization_id() -> Optional[uuid.UUID]:
    return _organization_id.get()


def get_current_campus_id() -> Optional[uuid.UUID]:
    return _campus_id.get()


def clear_tenant_context() -> None:
    """
    Clears all request and tenant state.
    Must be called in middleware finally blocks to guarantee request isolation.
    """
    _request_id.set(None)
    _trace_id.set(None)
    _organization_id.set(None)
    _campus_id.set(None)
    _actor_id.set(None)
