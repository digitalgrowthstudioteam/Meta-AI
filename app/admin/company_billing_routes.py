from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.admin.rbac import assert_admin_permission
from app.users.models import User
from app.billing.company_settings_service import CompanySettingsService

router = APIRouter(prefix="/billing/company-info", tags=["Admin Billing Info"])


@router.get("")
async def get_company_billing_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    # Admin enforcement
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    settings = await CompanySettingsService.get(db)

    return {
        "company_name": settings.company_name,
        "address_line1": settings.address_line1,
        "address_line2": settings.address_line2,
        "state": settings.state,
        "state_code": settings.state_code,
        "contact_email": settings.contact_email,
        "contact_phone": settings.contact_phone,
        "gst_registered": settings.gst_registered,
        "gstin": settings.gstin,
        "sac_code": settings.sac_code,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
    }


@router.post("")
async def update_company_billing_info(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    # Admin enforcement
    assert_admin_permission(admin_user=current_user, permission="billing:write")

    required_fields = ["company_name", "address_line1", "state", "state_code"]
    for field in required_fields:
        if field not in payload or not payload[field]:
            raise HTTPException(400, detail=f"{field} is required")

    # GST validation logic:
    gst_registered = payload.get("gst_registered", False)
    gstin = payload.get("gstin")

    if gst_registered and not gstin:
        raise HTTPException(400, detail="GSTIN is required when gst_registered=true")

    # Update
    settings = await CompanySettingsService.update(db, payload)

    return {"status": "ok", "updated_at": settings.updated_at.isoformat()}
