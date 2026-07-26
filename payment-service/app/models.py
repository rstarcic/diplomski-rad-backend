from datetime import datetime, timezone

from database import Base
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PaymentProfile(Base):
    __tablename__ = "payment_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    stripe_account_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    stripe_payment_method_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    charges_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    payouts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    details_submitted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    payment_setup_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    payout_setup_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    card_brand: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    card_last4: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
    )
    card_exp_month: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    card_exp_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    billing_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    billing_postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    billing_country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

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


class JobPayment(Base):
    __tablename__ = "job_payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'cancelled', 'overdue')",
            name="ck_job_payments_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    application_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    contractor_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    checkout_attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
