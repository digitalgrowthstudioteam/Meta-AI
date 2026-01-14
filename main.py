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
# ROUTERS (API ONLY)
# =========================
from app.auth.routes import router as auth_router
from app.campaigns.routes import router as campaigns_router
from app.meta_api.routes import router as meta_router
from app.meta_insights.routes import router as meta_insights_router
from app.reports.routes import router as reports_router
from app.dashboard.routes import router as dashboard_router
from app.ai_engine.routes import router as ai_router

# 🔥 FIXED: Use the REAL admin router (Contains Dashboard, Users, Invoices, Audit)
from app.admin.routes import router as admin_main_router

# 🆕 ADMIN CAMPAIGN EXPLORER
from app.admin.campaign_routes import router as admin_campaigns_router

# SPECIFIC ADMIN SUB-ROUTERS
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
# CORS MIDDLEWARE (ADDED)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for Phase 1 connectivity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(session_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(billing_router, prefix="/api")  # User Billing

# 🔥 ADMIN ROUTERS (FIXED ORDER)
app.include_router(admin_main_router, prefix="/api") # Main Admin (Dashboard, Users, Invoices)
app.include_router(admin_campaigns_router, prefix="/api") # Campaigns

# Feature Admin Routers
app.include_router(meta_router, prefix="/api")
app.include_router(meta_insights_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

# Analytics Admin Routers
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
# HEALTH CHECK
# =========================
@app.get("/api/health")
def health_check():
    return {"status": "ok"}
