"""
Digital Growth Studio (Meta-AI)
Main application entry point
"""

from fastapi import FastAPI

from app.auth.routes import router as auth_router


app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0"
)

# =========================
# ROUTERS
# =========================
app.include_router(auth_router)


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health_check():
    return {"status": "ok"}
