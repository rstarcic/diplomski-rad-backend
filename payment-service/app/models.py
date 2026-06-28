from datetime import datetime, timezone

from app.database import Base
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


def utc_now():
    return datetime.now(timezone.utc)


# TODO: Implement payment setup tracking.
# - For clients: store Stripe (or other provider) payment method setup status.
#   Set payment_setup_completed = True once the client adds a valid payment method.
# - For contractors: store payout account setup status (e.g. Stripe Connect onboarding).
#   Set payout_setup_completed = True once contractor completes payout onboarding.
# These flags should be exposed via GET /payments/status/{user_id} so the frontend
# can check whether to show the payment setup step during account setup flow.
class PaymentProfile(Base):
    __tablename__ = "payment_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # TODO: populate when client adds a payment method
    payment_setup_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # TODO: populate when contractor completes Stripe Connect (or equivalent) onboarding
    payout_setup_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
