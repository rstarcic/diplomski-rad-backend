import os
from datetime import UTC, datetime, timedelta

from errors import raise_auth_error
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RefreshSession, User
from app.schemas import LoginRequest, RegisterRequest, TokenPayload
from app.utils.security import (
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.utils.tokens import create_access_token

REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14))


def register_user(db: Session, data: RegisterRequest, role: str) -> User:
    existing_user = db.scalar(select(User).where(User.email == data.email))

    if existing_user is not None:
        raise_auth_error("email_already_registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=role,
        full_name=f"{data.first_name} {data.last_name}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, data: LoginRequest) -> tuple[User, str, str]:
    user = db.scalar(select(User).where(User.email == data.email))

    if (
        user is None
        or user.password_hash is None
        or not verify_password(data.password, user.password_hash)
    ):
        raise_auth_error("invalid_credentials")

    if not user.email_verified:
        raise_auth_error("account_not_verified")

    access_token, refresh_token = create_session(db, user)

    return user, access_token, refresh_token


def create_session(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(
        TokenPayload(
            sub=str(user.id),
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        )
    )

    refresh_token = generate_refresh_token()

    refresh_session = RefreshSession(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=(datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)),
    )

    db.add(refresh_session)
    db.commit()

    return access_token, refresh_token


def refresh_session(
    db: Session,
    old_refresh: str,
) -> tuple[str, str]:
    refresh_session_record = db.scalar(
        select(RefreshSession)
        .where(
            RefreshSession.token_hash == hash_token(old_refresh),
            RefreshSession.revoked.is_(False),
        )
        .with_for_update()
    )

    if (
        refresh_session_record is None
        or refresh_session_record.expires_at < datetime.now(UTC)
    ):
        raise_auth_error("refresh_token_expired")

    user = refresh_session_record.user
    new_refresh = generate_refresh_token()

    refresh_session_record.token_hash = hash_token(new_refresh)
    refresh_session_record.expires_at = datetime.now(UTC) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    db.commit()

    new_access_token = create_access_token(
        TokenPayload(
            sub=str(user.id),
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        )
    )

    return new_access_token, new_refresh


def revoke_session(db: Session, refresh_token: str) -> None:
    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_token(refresh_token),
            RefreshSession.revoked.is_(False),
        )
    )

    if session:
        session.revoked = True
        db.commit()
        db.commit()
