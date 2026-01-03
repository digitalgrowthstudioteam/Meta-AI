"""
Digital Growth Studio (Meta-AI)
Main application entry point

PHASE 1.6 — BACKEND UI CUTOVER
- FastAPI is API-only
- Legacy Jinja UI routes disabled (not deleted)
- /api/* is the single source of truth
"""

import app.models  # registers all SQLAlchemy models
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
# STATIC FILES (LEGACY — SAFE TO KEEP)
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
# TEMPLATE LOADER (LOGIN ONLY)
# =========================
templates = Jinja2Templates(directory="frontend")


# =========================
# LEGACY LOGIN PAGE (ONLY)
# =========================
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "shared/templates/login.html",
        {"request": request},
    )


# =========================
# API ROUTERS — SINGLE SOURCE
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
