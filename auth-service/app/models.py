from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from database import Base
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("role IN ('client', 'contractor')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)

    google_sub: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
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

    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        "RefreshSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(String, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_sessions",
    )


class OAuthPKCE(Base):
    __tablename__ = "oauth_pkce"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    flow_type: Mapped[str] = mapped_column(String(10), nullable=False)
    state: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    code_verifier: Mapped[str] = mapped_column(String, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
