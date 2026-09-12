"""
Standardized API Error Model and Exception Handler for Paraxis AI.
Complies with docs/api/error-model.md:
Returns unified error envelope with request_id, timestamp, details, and zero internal leakage.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from core.context import get_current_request_id

logger = logging.getLogger("paraxis.exceptions")


def _format_error_details(data: Any, prefix: str = "") -> List[Dict[str, str]]:
    """
    Recursively extract field and issue pairs from DRF validation error structures.
    """
    details = []
    if isinstance(data, dict):
        for field, issues in data.items():
            field_name = f"{prefix}.{field}" if prefix else str(field)
            details.extend(_format_error_details(issues, prefix=field_name))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                details.extend(_format_error_details(item, prefix=prefix))
            else:
                details.append({"field": prefix or "non_field_errors", "issue": str(item)})
    else:
        details.append({"field": prefix or "non_field_errors", "issue": str(data)})
    return details


def custom_exception_handler(exc: Exception, context: dict) -> Response:
    """
    Global DRF exception handler implementing the unified Paraxis AI error envelope.
    """
    request = context.get("request")
    request_id = get_current_request_id() or getattr(request, "request_id", "req_unknown")
    timestamp = datetime.now(timezone.utc).isoformat()

    # Call REST framework's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    # Convert Django's internal exceptions to DRF equivalents if unhandled
    if response is None:
        if isinstance(exc, Http404):
            exc = exceptions.NotFound(str(exc) or "Resource not found.")
            response = exception_handler(exc, context)
        elif isinstance(exc, DjangoValidationError):
            exc = exceptions.ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
            response = exception_handler(exc, context)

    if response is not None:
        # Determine standard error code
        code = "INTERNAL_ERROR"
        status_code = response.status_code

        if status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHENTICATED"
        elif status_code == status.HTTP_403_FORBIDDEN:
            code = "PERMISSION_DENIED"
        elif status_code == status.HTTP_404_NOT_FOUND:
            # Check if it was tenant-related
            detail_str = str(response.data) if response.data else ""
            if "tenant" in detail_str.lower() or "campus" in detail_str.lower() or "organization" in detail_str.lower():
                code = "TENANT_NOT_FOUND"
            else:
                code = "RESOURCE_NOT_FOUND"
        elif status_code == status.HTTP_400_BAD_REQUEST:
            code = "VALIDATION_FAILED"
        elif status_code == 422:
            code = "POLICY_VIOLATION"
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            code = "RATE_LIMIT_EXCEEDED"

        # Extract message and details
        details: List[Dict[str, str]] = []
        message = "An error occurred while processing your request."

        if isinstance(response.data, dict):
            if "detail" in response.data:
                message = str(response.data["detail"])
            else:
                message = "The request body or parameters failed validation."
                details = _format_error_details(response.data)
        elif isinstance(response.data, list):
            details = _format_error_details(response.data)

        envelope = {
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "timestamp": timestamp,
                "details": details,
            }
        }
        response.data = envelope
        return response

    # Unhandled internal 500 error - log full traceback internally, return sanitized envelope
    logger.exception(
        f"Unhandled server exception occurred. request_id={request_id} path={getattr(request, 'path', '')}",
        exc_info=exc,
    )

    envelope = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal server error occurred. Please contact support with the request ID.",
            "request_id": request_id,
            "timestamp": timestamp,
            "details": [],
        }
    }
    return Response(envelope, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
