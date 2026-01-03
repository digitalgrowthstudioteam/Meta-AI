from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/reports", tags=["Reports"])


# ---------------------------------------------------------
# REPORTS OVERVIEW
# ---------------------------------------------------------
@router.get("/overview")
async def reports_overview(
    current_user: User = Depends(get_current_user),
):
    """
    High-level reporting summary.
    Placeholder response — logic added later.
    """
    return {
        "status": "ok",
        "data": {
            "total_campaigns": 0,
            "ai_active_campaigns": 0,
            "lead_campaigns": 0,
            "sales_campaigns": 0,
        },
    }


# ---------------------------------------------------------
# CAMPAIGN REPORTS
# ---------------------------------------------------------
@router.get("/campaigns")
async def reports_campaigns(
    current_user: User = Depends(get_current_user),
):
    """
    Campaign-level reporting.
    Placeholder response — logic added later.
    """
    return {
        "status": "ok",
        "campaigns": [],
    }


# ---------------------------------------------------------
# PERFORMANCE REPORTS
# ---------------------------------------------------------
@router.get("/performance")
async def reports_performance(
    current_user: User = Depends(get_current_user),
):
    """
    Performance metrics reporting.
    Placeholder response — logic added later.
    """
    return {
        "status": "ok",
        "metrics": {
            "ctr": None,
            "cpl": None,
            "cpa": None,
            "roas": None,
        },
    }
