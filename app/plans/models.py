from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    monthly_price: Mapped[int] = mapped_column(Integer)

    max_ai_campaigns: Mapped[int] = mapped_column(Integer)
    max_ad_accounts: Mapped[int] = mapped_column(Integer)
    allows_addons: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
