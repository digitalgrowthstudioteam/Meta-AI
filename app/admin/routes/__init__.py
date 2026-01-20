from fastapi import APIRouter

# Core Admin Routers
from .dashboard_routes import router as dashboard_router
from .user_routes import router as user_router
from .billing_admin_routes import router as billing_router
from .risk_routes import router as risk_router
from .pricing_routes import router as pricing_router
from .meta_routes import router as meta_router
from .audit_routes import router as audit_router

# Main combined router for /admin/*
router = APIRouter(prefix="/admin", tags=["Admin"])

# Attach core admin routers (API only)
router.include_router(dashboard_router)
router.include_router(user_router)
router.include_router(billing_router)
router.include_router(risk_router)
router.include_router(pricing_router)
router.include_router(meta_router)
router.include_router(audit_router)
