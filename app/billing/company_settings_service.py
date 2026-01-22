from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.billing.company_settings_models import BillingCompanySettings


class CompanySettingsService:

    @staticmethod
    async def get(db: AsyncSession) -> BillingCompanySettings:
        row = await db.scalar(
            select(BillingCompanySettings)
            .where(BillingCompanySettings.singleton_key == 1)
            .limit(1)
        )
        if row:
            return row

        # Auto-seed minimal singleton row (non-GST mode)
        row = BillingCompanySettings(
            company_name="",
            address_line1="",
            state="Maharashtra",
            state_code="27",
            sac_code="998314",
            gst_registered=False,
            gstin=None,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return row

    @staticmethod
    async def update(db: AsyncSession, data: dict) -> BillingCompanySettings:
        row = await CompanySettingsService.get(db)

        for key, value in data.items():
            setattr(row, key, value)

        row.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(row)
        return row
