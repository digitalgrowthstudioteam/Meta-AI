"""
Digital Growth Studio (Meta-AI)
Main application entry point
API-only backend
"""

import app.models  # registers all SQLAlchemy models
from fastapi import FastAPI

# =========================
# ROUTERS (API ONLY)
# =========================
from app.auth.routes import router as auth_router
from app.campaigns.routes import router as campaigns_router
from app.admin.routes import router as admin_router
from app.meta_api.routes import router as meta_router
from app.reports.routes import router as reports_router


# =========================
# APP INITIALIZATION
# =========================
app = FastAPI(
    title="Digital Growth Studio API",
    description="Meta Ads AI Optimization Platform — API",
    version="0.1.0",
)


# =========================
# API ROUTERS (PREFIXED)
# =========================
app.include_router(auth_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(meta_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


# =========================
# HEALTH CHECK
# =========================
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
