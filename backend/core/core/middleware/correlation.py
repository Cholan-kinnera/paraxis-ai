"""
Correlation Middleware for Paraxis AI Core Platform.
Extracts or generates X-Request-ID and X-Trace-ID, sets request contextvars,
and stamps response headers for end-to-end distributed observability.
"""
import re
import uuid
from typing import Callable
from django.http import HttpRequest, HttpResponse
from core.context import (
    set_current_request_id,
    set_current_trace_id,
    get_current_request_id,
    get_current_trace_id,
)

SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{8,64}$")


def _sanitize_or_generate_id(header_val: str, prefix: str) -> str:
    if header_val and SAFE_ID_REGEX.match(header_val.strip()):
        return header_val.strip()
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class CorrelationMiddleware:
    """
    Middleware that ensures every inbound request has an isolated request_id and trace_id.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming_req_id = request.META.get("HTTP_X_REQUEST_ID", "")
        incoming_trace_id = request.META.get("HTTP_X_TRACE_ID", "")

        req_id = _sanitize_or_generate_id(incoming_req_id, "req")
        trc_id = _sanitize_or_generate_id(incoming_trace_id, "trc")

        set_current_request_id(req_id)
        set_current_trace_id(trc_id)

        # Attach to request for convenient access in views and exception handlers
        request.request_id = req_id
        request.trace_id = trc_id

        response = self.get_response(request)

        response["X-Request-ID"] = req_id
        response["X-Trace-ID"] = trc_id
        return response
