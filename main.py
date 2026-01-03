"""
Digital Growth Studio (Meta-AI)
Main application entry point

PHASE 1.7 — API-ONLY MODE (LOCKED)

RULES:
- FastAPI serves APIs ONLY
- NO HTML rendering
- NO /login, /dashboard, or UI routes
- Next.js is the ONLY frontend
"""

import app.models  # registers all SQLAlchemy models

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# =========================
# ROUTERS (API ONLY)
# =========================
from app.auth.routes import router as auth_router
from app.campaigns.routes import router as campaigns_router
from app.admin.routes import router as admin_router
from app.meta_api.routes import router as meta_router
from app.reports.routes import router as reports_router
from app.dashboard.routes import router as dashboard_router


# =========================
# APP INITIALIZATION
# =========================
app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0",
)


# =========================
# STATIC FILES (OPTIONAL)
# Can be removed later if unused
# =========================
app.mount(
    "/static/shared",
    StaticFiles(directory="frontend/shared/assets"),
    name="static-shared",
)

app.mount(
    "/static/user",
    StaticFiles(directory="frontend/user/assets"),
    name="static-user",
)

app.mount(
    "/static/admin",
    StaticFiles(directory="frontend/admin/assets"),
    name="static-admin",
)


# =========================
# API ROUTERS — SINGLE SOURCE OF TRUTH
# =========================
app.include_router(auth_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(meta_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


# =========================
# HEALTH CHECK (API SAFE)
# =========================
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
