from fastapi import APIRouter

from .dashboard_routes import router as dashboard_router
from .user_routes import router as user_router
from .billing_admin_routes import router as billing_router
from .company_billing_routes import router as company_billing_router
from .plan_routes import router as plan_router
from .risk_routes import router as risk_router
from .pricing_routes import router as pricing_router
from .meta_routes import router as meta_router
from .audit_routes import router as audit_router

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(dashboard_router)
router.include_router(user_router)
router.include_router(billing_router)
router.include_router(company_billing_router)
router.include_router(plan_router)       # 👈 now officially placed & active
router.include_router(pricing_router)
router.include_router(risk_router)
router.include_router(meta_router)
router.include_router(audit_router)
