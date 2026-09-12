"""
Audit Service for recording security-critical events and entity mutations.
Guarantees append-only persistence to the immutable AuditLog model.
"""
from typing import Optional
import logging
from django.http import HttpRequest
from core.context import (
    get_current_actor_id,
    get_current_organization_id,
    get_current_campus_id,
)
from core.models.audit import AuditLog, ActorType

logger = logging.getLogger(__name__)


def get_client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    """
    Extract client IP address from standard headers or REMOTE_ADDR.
    """
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
        return ip
    return request.META.get("REMOTE_ADDR")


def log_audit_event(
    action: str,
    entity_type: str,
    entity_id: str,
    actor=None,
    actor_type: str = ActorType.USER,
    organization=None,
    campus=None,
    ip_address: Optional[str] = None,
    pre_state: Optional[dict] = None,
    post_state: Optional[dict] = None,
    request: Optional[HttpRequest] = None,
) -> AuditLog:
    """
    Persist an immutable audit log record.
    Automatically enriches missing tenant or actor context from the active request context.
    """
    if request and not ip_address:
        ip_address = get_client_ip(request)

    # Resolve actor if omitted
    actor_id = None
    if actor:
        actor_id = getattr(actor, "id", actor)
    else:
        actor_id = get_current_actor_id()

    # Resolve organization if omitted
    org_id = None
    if organization:
        org_id = getattr(organization, "id", organization)
    elif actor and hasattr(actor, "organization_id") and actor.organization_id:
        org_id = actor.organization_id
    else:
        org_id = get_current_organization_id()

    # Resolve campus if omitted
    campus_id = None
    if campus:
        campus_id = getattr(campus, "id", campus)
    elif actor and hasattr(actor, "primary_campus_id") and actor.primary_campus_id:
        campus_id = actor.primary_campus_id
    else:
        campus_id = get_current_campus_id()

    audit_entry = AuditLog(
        organization_id=org_id,
        campus_id=campus_id,
        actor_id=actor_id,
        actor_type=actor_type,
        ip_address=ip_address,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        pre_state_json=pre_state or {},
        post_state_json=post_state or {},
    )
    audit_entry.save()
    return audit_entry
