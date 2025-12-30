from datetime import datetime
import uuid

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Plan(Base):
    """
    System-owned plan definitions.
    Plans define WHAT is allowed.
    They never expire.
    """

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False)  # paise

    a
