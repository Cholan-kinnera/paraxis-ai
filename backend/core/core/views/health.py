"""
Health check view for Paraxis AI Core Platform.
"""
from datetime import datetime, timezone
from django.http import JsonResponse

def health_check(request):
    """
    Readiness and liveness probe for the Django Core Platform.
    Returns HTTP 200 with service metadata.
    """
    return JsonResponse(
        {
            "status": "healthy",
            "service": "paraxis-core",
            "version": "0.1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": request.META.get("DJANGO_SETTINGS_MODULE", "config.settings"),
        },
        status=200,
    )
