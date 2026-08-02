from datetime import UTC, datetime

from database import Base
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def utc_now():
    return datetime.now(UTC)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "reviewer_id",
            name="uq_reviews_job_reviewer",
        ),
        Index(
            "ix_reviews_target",
            "target_type",
            "target_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=True,
        index=True,
    )
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.user_id"), nullable=False
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.user_id"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    communication_rating: Mapped[float] = mapped_column(Float, nullable=False)
    clarity_rating: Mapped[float] = mapped_column(Float, nullable=False)
    reliability_rating: Mapped[float] = mapped_column(Float, nullable=False)
    collaboration_rating: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    reviewer = relationship("Profile", foreign_keys=[reviewer_id])
    target = relationship("Profile", foreign_keys=[target_id])
