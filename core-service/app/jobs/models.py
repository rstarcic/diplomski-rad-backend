from datetime import UTC, datetime

from database import Base
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    desc,
)
from sqlalchemy.orm import Mapped, mapped_column


def utc_now():
    return datetime.now(UTC)


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        UniqueConstraint(
            "source_job_id",
            name="uq_jobs_source_job_id",
        ),
        CheckConstraint(
            "location_type IN ('on_site', 'hybrid', 'remote')",
            name="ck_jobs_location_type",
        ),
        CheckConstraint(
            "budget_type IN ('fixed', 'hourly')",
            name="ck_jobs_budget_type",
        ),
        CheckConstraint(
            "status IN ('open', 'awaiting_contract', 'in_progress', 'done_by_contractor', 'completed_by_client', 'incomplete', 'cancelled')",
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
        Index(
            "ix_jobs_open_deadline_created",
            "status",
            "deadline",
            desc("created_at"),
        ),
        Index(
            "ix_jobs_client_status",
            "client_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(nullable=False)
    source_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    deliverables: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    budget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    budget_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="EUR")

    duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    hours_per_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

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
