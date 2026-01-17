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
from fastapi.middleware.cors import CORSMiddleware

# =========================
# NEW IMPORTS FOR AUTO-ADMIN
# =========================
from sqlalchemy import select
from app.users.models import User
from app.core.db_session import AsyncSessionLocal

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

# 🔥 REAL admin router
from app.admin.routes import router as admin_main_router

# Admin extra routers
from app.admin.campaign_routes import router as admin_campaigns_router
from app.admin.revenue_routes import router as admin_revenue_router
from app.admin.revenue_breakdown_routes import router as admin_revenue_breakdown_router
from app.admin.revenue_monthly_routes import router as admin_revenue_monthly_router
from app.admin.revenue_sanity_routes import router as admin_revenue_sanity_router
from app.admin.billing_health_routes import router as admin_billing_health_router
from app.admin.user_billing_snapshot_routes import router as admin_user_billing_router
from app.admin.billing_timeline_routes import router as admin_billing_timeline_router
from app.admin.user_ai_usage_routes import router as admin_user_ai_router
from app.admin.ai_limit_dashboard_routes import router as admin_ai_limit_router
from app.admin.ai_force_deactivate_routes import router as admin_ai_force_router

# 🌍 SESSION CONTEXT
from app.auth.session_routes import router as session_router
from app.auth.session_routes import api_router as session_api_router
from app.billing.routes import router as billing_router

# =========================
# APP INITIALIZATION
# =========================
app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0",
)

# =========================
# CORS MIDDLEWARE
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STATIC FILES (UNUSED)
# =========================
app.mount(
    "/static",
    StaticFiles(directory="frontend_next", check_dir=False),
    name="static",
)

# =========================
# API ROUTERS — SINGLE SOURCE
# =========================

# Auth / Session
app.include_router(auth_router)
app.include_router(session_router, prefix="/api")
app.include_router(session_api_router, prefix="/api")  # enables /api/session/context
app.include_router(campaigns_router, prefix="/api")
app.include_router(billing_router, prefix="/api")

# Admin Core
app.include_router(admin_main_router, prefix="/api")
app.include_router(admin_campaigns_router, prefix="/api")

# Meta / Insights / Reporting
app.include_router(meta_router, prefix="/api")
app.include_router(meta_insights_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

# Admin Analytics Layer
app.include_router(admin_user_billing_router, prefix="/api")
app.include_router(admin_revenue_router, prefix="/api")
app.include_router(admin_revenue_breakdown_router, prefix="/api")
app.include_router(admin_revenue_monthly_router, prefix="/api")
app.include_router(admin_revenue_sanity_router, prefix="/api")
app.include_router(admin_billing_health_router, prefix="/api")
app.include_router(admin_billing_timeline_router, prefix="/api")
app.include_router(admin_user_ai_router, prefix="/api")
app.include_router(admin_ai_limit_router, prefix="/api")
app.include_router(admin_ai_force_router, prefix="/api")

# =========================
# AUTO-ADMIN PROMOTION LOGIC
# =========================
async def ensure_default_admin():
    target_email = "digitalgrowthstudioteam@gmail.com"

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.email == target_email))
            user = result.scalar_one_or_none()

            if user:
                if user.role != "admin":
                    print(f"🚀 Promoting {target_email} to ADMIN...")
                    user.role = "admin"
                    await db.commit()
                    print(f"✅ {target_email} is now an ADMIN.")
                else:
                    print(f"ℹ️ {target_email} is already an Admin.")
            else:
                print(f"⚠️ Admin Check: User {target_email} not found. Please Sign Up first.")
    except Exception as e:
        print(f"❌ Failed to ensure admin: {e}")


@app.on_event("startup")
async def startup_event():
    await ensure_default_admin()

# =========================
# HEALTH CHECK
# =========================
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
