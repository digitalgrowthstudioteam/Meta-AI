from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.admin.rbac import assert_admin_permission
from app.billing.company_settings_models import BillingCompanySettings

router = APIRouter(prefix="/billing/company", tags=["Admin Billing Company"])


ALLOWED_UPDATE_ROLES = {"admin", "super_admin", "billing_admin"}


def require_company_admin(user: User):
    if user.role not in ALLOWED_UPDATE_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("")
async def get_company_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_company_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    row = await db.scalar(
        select(BillingCompanySettings)
        .where(BillingCompanySettings.singleton_key == 1)
        .limit(1)
    )

    if not row:
        return None

    return {
        "company_name": row.company_name,
        "address_line1": row.address_line1,
        "address_line2": row.address_line2,
        "state": row.state,
        "state_code": row.state_code,
        "contact_email": row.contact_email,
        "contact_phone": row.contact_phone,
        "gst_registered": row.gst_registered,
        "gstin": row.gstin,
        "sac_code": row.sac_code,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.post("")
async def upsert_company_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_company_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:write")

    gst_registered = bool(payload.get("gst_registered", False))

    gstin = payload.get("gstin")
    company_name = payload.get("company_name")
    state = payload.get("state")
    state_code = payload.get("state_code")

    if gst_registered:
        if not gstin or not company_name or not state or not state_code:
            raise HTTPException(400, detail="gstin, company_name, state, state_code required when gst_registered=True")

    row = await db.scalar(
        select(BillingCompanySettings)
        .where(BillingCompanySettings.singleton_key == 1)
        .limit(1)
    )

    if row:
        row.company_name = company_name or row.company_name
        row.address_line1 = payload.get("address_line1", row.address_line1)
        row.address_line2 = payload.get("address_line2", row.address_line2)
        row.state = state or row.state
        row.state_code = state_code or row.state_code
        row.contact_email = payload.get("contact_email", row.contact_email)
        row.contact_phone = payload.get("contact_phone", row.contact_phone)
        row.gst_registered = gst_registered
        row.gstin = gstin if gst_registered else None
        row.sac_code = payload.get("sac_code", row.sac_code)
        row.updated_at = datetime.utcnow()
    else:
        row = BillingCompanySettings(
            company_name=company_name or "",
            address_line1=payload.get("address_line1", ""),
            address_line2=payload.get("address_line2"),
            state=state or "",
            state_code=state_code or "",
            contact_email=payload.get("contact_email"),
            contact_phone=payload.get("contact_phone"),
            gst_registered=gst_registered,
            gstin=gstin if gst_registered else None,
            sac_code=payload.get("sac_code"),
        )
        db.add(row)

    await db.commit()
    return {"status": "ok"}
