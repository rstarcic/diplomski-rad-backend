from datetime import datetime, timezone

from database import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def utc_now():
    return datetime.now(timezone.utc)


class Negotiation(Base):
    __tablename__ = "negotiations"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_client', 'pending_contractor', 'accepted', 'rejected', 'expired')",
            name="ck_negotiations_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        unique=True,
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id"),
        nullable=False,
        unique=True,
    )
    client_id: Mapped[int] = mapped_column(nullable=False, index=True)
    contractor_id: Mapped[int] = mapped_column(nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False)

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
    edits: Mapped[list["NegotiationEdit"]] = relationship(
        back_populates="negotiation",
        cascade="all, delete-orphan",
        order_by="NegotiationEdit.round_number",
    )


class NegotiationEdit(Base):
    __tablename__ = "negotiation_edits"

    __table_args__ = (
        CheckConstraint(
            "budget_type IN ('fixed', 'hourly')",
            name="ck_negotiation_edits_budget_type",
        ),
        CheckConstraint(
            "budget_amount > 0",
            name="ck_negotiation_edits_budget_amount_positive",
        ),
        UniqueConstraint(
            "negotiation_id",
            "round_number",
            name="uq_negotiation_edits_round",
        ),
        CheckConstraint(
            "submitted_by IN ('client', 'contractor')",
            name="ck_negotiation_edits_submitted_by",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    negotiation_id: Mapped[int] = mapped_column(
        ForeignKey("negotiations.id"),
        nullable=False,
    )

    round_number: Mapped[int] = mapped_column(nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(20), nullable=False)

    budget_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)

    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    deliverables: Mapped[str | None] = mapped_column(Text, nullable=True)

    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    negotiation: Mapped["Negotiation"] = relationship(
        back_populates="edits",
    )
