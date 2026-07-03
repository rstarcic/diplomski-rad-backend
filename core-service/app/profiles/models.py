import base64
from datetime import datetime, timezone
from typing import Optional

from database import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


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
    profile_picture_blob: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary, nullable=True
    )
    profile_picture_content_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    profile_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    skills: Mapped[list["ContractorSkill"]] = relationship(
        "ContractorSkill",
        back_populates="contractor",
        cascade="all, delete-orphan",
    )
    portfolio_items: Mapped[list["PortfolioItem"]] = relationship(
        "PortfolioItem",
        back_populates="contractor",
        cascade="all, delete-orphan",
    )

    @property
    def display_profile_picture(self) -> str | None:
        if self.profile_picture_blob is None:
            return self.profile_picture

        content_type = self.profile_picture_content_type or "image/jpeg"
        encoded_picture = base64.b64encode(self.profile_picture_blob).decode("ascii")
        return f"data:{content_type};base64,{encoded_picture}"


class ContractorSkill(Base):
    __tablename__ = "contractor_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    contractor_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.user_id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    contractor = relationship("Profile", back_populates="skills")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    contractor_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.user_id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    project_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    contractor = relationship("Profile", back_populates="portfolio_items")
