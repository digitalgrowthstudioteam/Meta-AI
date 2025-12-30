"""
Digital Growth Studio (Meta-AI)
Main application entry point
"""

from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.campaigns.routes import router as campaigns_router
from app.admin.routes import router as admin_router


app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0",
)

# =========================
# ROUTERS
# =========================
app.include_router(auth_router)
app.include_router(campaigns_router)
app.include_router(admin_router)


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health_check():
    return {"status": "ok"}
