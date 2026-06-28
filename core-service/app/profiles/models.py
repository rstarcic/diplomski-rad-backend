from datetime import datetime, timezone
from typing import Optional

from app.database import Base
from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column


def utc_now():
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"

    __table_args__ = (
        CheckConstraint("role IN ('client', 'contractor')", name="ck_profiles_role"),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
