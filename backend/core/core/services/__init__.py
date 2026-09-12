"""
Domain services package for Paraxis AI Core Platform.
"""
from core.services.audit import log_audit_event, get_client_ip

__all__ = [
    "log_audit_event",
    "get_client_ip",
]
