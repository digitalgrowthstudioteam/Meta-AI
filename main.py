"""
Digital Growth Studio (Meta-AI)
Main application entry point

PHASE 1.8 — SINGLE CONTEXT SOURCE
- FastAPI is API-only
- ONE session context for all pages
- Next.js owns ALL UI routes
"""

import app.models  # registers all SQLAlchemy models
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# =========================
# ROUTERS (API ONLY)
# =========================
from app.auth.routes import router as auth_router
from app.campaigns.routes import router as campaigns_router
from app.meta_api.routes import router as meta_router
from app.meta_insights.routes import router as meta_insights_router
from app.reports.routes import router as reports_router
from app.dashboard.routes import router as dashboard_router
from app.ai_engine.routes import router as ai_router
from backend.app.admin.dashboard_routes import router as admin_dashboard_router
from backend.app.admin.users_routes import router as admin_users_router

# 🔒 ADMIN (IMPERSONATION)
from backend.app.admin.impersonation_routes import router as admin_router

# 🌍 SESSION CONTEXT
from app.auth.session_routes import router as session_router


# =========================
# APP INITIALIZATION
# =========================
app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0",
)


# =========================
# STATIC FILES (KEEP — UNUSED)
# =========================
app.mount(
    "/static",
    StaticFiles(directory="frontend", check_dir=False),
    name="static",
)


# =========================
# API ROUTERS — SINGLE SOURCE
# =========================
app.include_router(auth_router, prefix="/api")
app.include_router(session_router, prefix="/api")   # 🔑 /api/session/context
app.include_router(campaigns_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(meta_router, prefix="/api")
app.include_router(meta_insights_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(admin_dashboard_router, prefix="/api")
app.include_router(admin_users_router, prefix="/api")

# =========================
# HEALTH CHECK
# =========================
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
