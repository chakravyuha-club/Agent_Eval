from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.competition import router as comp_router
from app.api.submissions import router as sub_router
from app.api.leaderboard import router as lb_router
from app.api.admin import router as admin_router
from app.services.seed_data import seed_database

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Dimensional AI Agent Evaluation & Competition Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(comp_router, prefix="/api")
app.include_router(sub_router, prefix="/api")
app.include_router(lb_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    """Auto-initialize and seed 50 teams on startup if required."""
    seed_database()

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}

@app.get("/", tags=["System"])
def root():
    return {
        "name": settings.APP_NAME,
        "description": "Multi-Dimensional AI Agent Evaluation Platform",
        "docs": "/docs",
        "api_health": "/health"
    }
