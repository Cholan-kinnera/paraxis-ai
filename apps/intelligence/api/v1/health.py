"""
Health probe endpoint for Paraxis AI Intelligence Platform.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    provider: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Readiness and liveness probe for the FastAPI Intelligence Platform.
    """
    from apps.intelligence.config import settings
    return HealthResponse(
        status="healthy",
        service="paraxis-intelligence",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        provider=settings.AI_DEFAULT_PROVIDER,
    )
