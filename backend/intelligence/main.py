import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.intelligence.config import settings
    from backend.intelligence.api.v1.health import router as health_router
    from backend.intelligence.api.v1.orchestrate import router as orchestrate_router
    from backend.intelligence.api.v1.tools import router as tools_router
except ImportError:
    from config import settings
    from api.v1.health import router as health_router
    from api.v1.orchestrate import router as orchestrate_router
    from api.v1.tools import router as tools_router

app = FastAPI(
    title="Paraxis AI Intelligence Platform",
    description="Agentic orchestration, operational RAG, and reasoning workflows for Paraxis AI.",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Correlation Tracing Middleware
@app.middleware("http")
async def correlation_tracing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    trace_id = request.headers.get("X-Trace-ID", f"trace_{uuid.uuid4().hex[:16]}")
    tenant_id = request.headers.get("X-Tenant-ID", "")

    request.state.request_id = req_id
    request.state.trace_id = trace_id
    request.state.tenant_id = tenant_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Trace-ID"] = trace_id
    if tenant_id:
        response.headers["X-Tenant-ID"] = tenant_id
    return response

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
app.include_router(orchestrate_router, prefix="/api/v1", tags=["Orchestration"])
app.include_router(tools_router, prefix="/api/v1", tags=["Tools"])

@app.get("/")
async def root():
    return {
        "message": "Paraxis AI Intelligence Platform",
        "status": "online",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }

