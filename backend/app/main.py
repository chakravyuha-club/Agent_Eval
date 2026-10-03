from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.competition import router as comp_router
from app.api.submissions import router as sub_router
from app.api.leaderboard import router as lb_router
from app.api.admin import router as admin_router
from app.api.snapshots import router as snapshots_router
from app.services.seed_data import seed_database

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Dimensional AI Agent Evaluation & Competition Platform",
    version="1.0.0",
    docs_url=None if settings.ENVIRONMENT.lower() == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT.lower() == "production" else "/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/api")
app.include_router(comp_router, prefix="/api")
app.include_router(sub_router, prefix="/api")
app.include_router(lb_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(snapshots_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    """Create tables; seed demo data ONLY when SEED_DEMO_DATA is enabled (never in production)."""
    if settings.SEED_DEMO_DATA:
        seed_database()
    else:
        from app.db.session import Base, engine
        Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["System"])
def health():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "evaluator_version": settings.EVALUATOR_VERSION
    }
