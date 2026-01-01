"""
Digital Growth Studio (Meta-AI)
Main application entry point
"""

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# =========================
# AUTH DEPENDENCY
# =========================
from app.auth.dependencies import require_user
from app.users.models import User

# =========================
# ROUTERS
# =========================
from app.auth.routes import router as auth_router
from app.campaigns.routes import router as campaigns_router
from app.admin.routes import router as admin_router
from app.meta_api.routes import router as meta_router


# =========================
# APP INITIALIZATION
# =========================
app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0",
)


# =========================
# FRONTEND — STATIC FILES
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
# FRONTEND — SINGLE TEMPLATE LOADER (CRITICAL)
# =========================
templates = Jinja2Templates(directory="frontend")


# =========================
# UI ROUTES (NO LOGIC)
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
    """
    User dashboard UI.
    Requires authenticated session.
    """
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
    """
    Campaign list UI.
    Data will be connected later.
    """
    return user_templates.TemplateResponse(
        "campaigns.html",
        {
            "request": request,
            "user": current_user,
        },
    )

@app.get("/ai-actions")
def ai_actions_page(
    request: Request,
    current_user: User = Depends(require_user),
):
    """
    AI action history UI.
    Shows explainable ML actions.
    """
    return user_templates.TemplateResponse(
        "ai_actions.html",
        {
            "request": request,
            "user": current_user,
        },
    )

# =========================
# API ROUTERS
# =========================
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(admin_router)
app.include_router(meta_router)


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health_check():
    return {"status": "ok"}
