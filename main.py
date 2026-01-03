"""
Digital Growth Studio (Meta-AI)
Main application entry point
SAFE MODE:
- Legacy Jinja UI preserved
- API routes duplicated under /api
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
# FRONTEND — STATIC FILES (LEGACY UI)
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
# FRONTEND — TEMPLATE LOADER (LEGACY UI)
# =========================
templates = Jinja2Templates(directory="frontend")


# =========================
# UI ROUTES — LEGACY (DO NOT REMOVE YET)
# =========================

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "shared/templates/login.html",
        {"request": request},
    )


@app.get("/dashboard")
def dashboard_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/dashboard.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/campaigns")
def campaigns_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/campaigns.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/ai/actions")
def ai_actions_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/ai_actions.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/audience/insights")
def audience_insights_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/audience_insights.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/campaigns/buy")
def buy_campaign_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/buy_campaign.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/billing")
def billing_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/billing.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/settings")
def settings_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/settings.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@app.get("/reports")
def reports_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    return templates.TemplateResponse(
        "user/templates/reports.html",
        {
            "request": request,
            "user": current_user,
        },
    )


# =========================
# API ROUTERS — LEGACY (UNCHANGED)
# =========================
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(admin_router)
app.include_router(meta_router)
app.include_router(reports_router)
app.include_router(dashboard_router)


# =========================
# API ROUTERS — NEW /api PREFIX (SAFE MODE)
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
