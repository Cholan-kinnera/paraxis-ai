"""
Tenancy Middleware for Paraxis AI Core Platform.
Guarantees tenant isolation by establishing request-scoped tenant context
and enforcing tenant context cleanup after every request lifecycle.
"""
from typing import Callable
import uuid
from django.http import HttpRequest, HttpResponse
from core.context import (
    set_current_tenant,
    set_current_actor_id,
    clear_tenant_context,
)


class TenancyMiddleware:
    """
    Middleware that manages the lifecycle of tenant context.
    Clears tenant context unconditionally in a finally block to prevent context leakage.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            # If request.user is already authenticated (e.g. session or custom auth)
            user = getattr(request, "user", None)
            if user and user.is_authenticated and user.is_active:
                org_id = user.organization_id
                campus_id = user.primary_campus_id

                # Check if caller requested a specific campus context via header
                requested_campus_id = request.META.get("HTTP_X_CAMPUS_ID")
                if requested_campus_id:
                    try:
                        campus_uuid = uuid.UUID(requested_campus_id)
                        from core.models.organization import Campus
                        if user.is_superuser:
                            campus_id = campus_uuid
                        elif Campus.objects.filter(id=campus_uuid, organization_id=org_id).exists():
                            campus_id = campus_uuid
                    except (ValueError, TypeError):
                        pass

                set_current_tenant(org_id, campus_id)
                set_current_actor_id(user.id)

            response = self.get_response(request)
            return response
        finally:
            # Absolute invariant: Clear tenant context after every request
            clear_tenant_context()
