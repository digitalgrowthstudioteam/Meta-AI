"""
Digital Growth Studio (Meta-AI)
Main application entry point
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
# FRONTEND — TEMPLATES
# =========================
shared_templates = Jinja2Templates(directory="frontend/shared/templates")
user_templates = Jinja2Templates(directory="frontend/user/templates")
admin_templates = Jinja2Templates(directory="frontend/admin/templates")


# =========================
# UI ROUTES (NO LOGIC)
# =========================
@app.get("/login")
def login_page(request: Request):
    return shared_templates.TemplateResponse(
        "login.html",
        {"request": request},
    )


# =========================
# ROUTERS
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
