from datetime import datetime, timezone

from database import Base
from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Contract(Base):
    __tablename__ = "contracts"

    __table_args__ = (
        CheckConstraint(
            "budget_amount > 0",
            name="ck_contracts_budget_positive",
        ),
        CheckConstraint(
            "duration > 0",
            name="ck_contracts_duration_positive",
        ),
        CheckConstraint(
            "hours_per_week > 0 AND hours_per_week <= 168",
            name="ck_contracts_hours_per_week_valid",
        ),
        CheckConstraint(
            "budget_type IN ('fixed', 'hourly')",
            name="ck_contracts_budget_type",
        ),
        CheckConstraint(
            "status IN ("
            "'pending_signatures', "
            "'pending_client_signature', "
            "'pending_contractor_signature', "
            "'active', "
            "'completed', "
            "'cancelled'"
            ")",
            name="ck_contracts_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    contract_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    platform_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="WorkLink",
    )

    application_id: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )

    negotiation_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Klijent snapshot
    client_id: Mapped[int] = mapped_column(nullable=False)
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_email: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(30))
    client_country: Mapped[str | None] = mapped_column(String(100))
    client_city: Mapped[str | None] = mapped_column(String(100))

    # Contractor snapshot
    contractor_id: Mapped[int] = mapped_column(nullable=False)
    contractor_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    contractor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    contractor_phone: Mapped[str | None] = mapped_column(String(30))
    contractor_country: Mapped[str | None] = mapped_column(String(100))
    contractor_city: Mapped[str | None] = mapped_column(String(100))

    # Job snapshot
    job_id: Mapped[int] = mapped_column(nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Dogovoreni uvjeti
    budget_amount: Mapped[float] = mapped_column(Float, nullable=False)
    budget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="EUR",
    )

    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    deliverables: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending_signatures",
    )

    client_signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    client_signature_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    contractor_signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    contractor_signature_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
