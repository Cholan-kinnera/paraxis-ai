"""
Authentication package for Paraxis AI Core Platform.
"""
from core.authentication.jwt import (
    JWTAuthentication,
    generate_access_token,
    generate_refresh_token,
    decode_token,
)

__all__ = [
    "JWTAuthentication",
    "generate_access_token",
    "generate_refresh_token",
    "decode_token",
]
