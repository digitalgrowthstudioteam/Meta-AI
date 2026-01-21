from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db_session import get_db
from sqlalchemy import select
from app.plans.models import Plan

router = APIRouter(prefix="/public", tags=["Public Plans"])

@router.get("/plans")
async def public_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Plan).where(Plan.is_active == True, Plan.is_hidden == False)
    )
    plans = result.scalars().all()
    return [
        {
            "name": p.name,
            "code": p.name.lower(),
            "monthly_price": p.monthly_price,
            "yearly_price": p.yearly_price,
            "yearly_allowed": p.yearly_allowed,
            "auto_allowed": p.auto_allowed,
            "manual_allowed": p.manual_allowed,
            "currency": "INR",
            "ai_limit": p.max_ai_campaigns,
        }
        for p in plans
    ]
