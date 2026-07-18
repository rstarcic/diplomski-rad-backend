from datetime import datetime, timezone

from database import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


def utc_now():
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'selected', 'accepted', 'rejected', 'withdrawn')",
            name="ck_applications_status",
        ),
        UniqueConstraint(
            "job_id",
            "contractor_id",
            name="uq_applications_job_contractor",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    contractor_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.user_id"), nullable=False
    )

    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
