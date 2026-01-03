"""
Digital Growth Studio (Meta-AI)
Main application entry point

PHASE 1.6 — BACKEND UI CUTOVER
- FastAPI is API-only
- Legacy Jinja UI routes disabled (not deleted)
- /api/* remains source of truth
"""

import app.models  # registers all SQLAlchemy models
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# =========================
# AUTH DEPENDENCY
# =========================
from app.auth.dependencies import require_user
from app.users.models import User

# =========================
# ROUTERS (API LOGIC)
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
# FRONTEND — STATIC FILES (LEGACY, KEPT FOR NOW)
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
# TEMPLATE LOADER (LEGACY, KEPT FOR LOGIN ONLY)
# =========================
templates = Jinja2Templates(directory="frontend")


# =========================
# UI ROUTES — ONLY LOGIN (LEGACY)
# =========================
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "shared/templates/login.html",
        {"request": request},
    )


# =========================
# API ROUTERS — CANONICAL
# =========================
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(admin_router)
app.include_router(meta_router)
app.include_router(reports_router)
app.include_router(dashboard_router)


# =========================
# API ROUTERS — /api PREFIX
# =========================
app.include_router(auth_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(meta_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health_check():
    return {"status": "ok"}
