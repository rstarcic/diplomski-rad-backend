from datetime import datetime, timezone

from database import Base
from sqlalchemy import JSON, CheckConstraint, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column


def utc_now():
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint(
            "location_type IN ('on_site', 'hybrid', 'remote')",
            name="ck_jobs_location_type",
        ),
        CheckConstraint(
            "budget_type IN ('fixed', 'hourly')",
            name="ck_jobs_budget_type",
        ),
        CheckConstraint(
            "status IN ('open', 'in_progress', 'done_by_contractor', 'completed_by_client', 'incomplete', 'cancelled')",
            name="ck_jobs_status",
        ),
        CheckConstraint(
            "budget_amount > 0",
            name="ck_jobs_budget_amount_positive",
        ),
        CheckConstraint(
            "currency = 'EUR'",
            name="ck_jobs_currency_eur",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    deliverables: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    budget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    budget_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")

    duration: Mapped[str] = mapped_column(String(50), nullable=False)
    hours_per_week: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")

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
