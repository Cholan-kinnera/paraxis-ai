"""
Paraxis AI Intelligence Platform — FastAPI Entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    from backend.intelligence.config import settings
    from backend.intelligence.api.v1.health import router as health_router
except ImportError:
    from config import settings
    from api.v1.health import router as health_router

app = FastAPI(
    title="Paraxis AI Intelligence Platform",
    description="Agentic orchestration, operational RAG, and reasoning workflows for Paraxis AI.",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 routes
app.include_router(health_router, prefix="/api/v1", tags=["System"])

@app.get("/")
async def root():
    return {
        "message": "Paraxis AI Intelligence Platform",
        "status": "online",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }
