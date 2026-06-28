import os
from datetime import datetime, timedelta, timezone

from errors import raise_auth_error
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
    if db.query(User).filter(User.email == data.email).first():
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
    user = db.query(User).filter(User.email == data.email).first()
    if (
        not user
        or not user.password_hash
        or not verify_password(data.password, user.password_hash)
    ):
        raise_auth_error("invalid_credentials")

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
    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    session = db.query(RefreshSession).filter(RefreshSession.user_id == user.id).first()
    if session:
        session.token_hash = token_hash
        session.expires_at = expires_at
        session.revoked = False
    else:
        db.add(
            RefreshSession(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at
            )
        )

    db.commit()
    return access_token, refresh_token


def refresh_session(db: Session, old_refresh: str) -> tuple[str, str]:
    session = (
        db.query(RefreshSession)
        .filter(
            RefreshSession.token_hash == hash_token(old_refresh),
            RefreshSession.revoked.is_(False),
        )
        .first()
    )
    if not session or session.expires_at < datetime.now(timezone.utc):
        raise_auth_error("refresh_token_expired")

    user = session.user
    new_refresh = generate_refresh_token()
    session.token_hash = hash_token(new_refresh)
    session.expires_at = datetime.now(timezone.utc) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )
    db.commit()

    new_access = create_access_token(
        TokenPayload(
            sub=str(user.id),
            email=user.email,
            role=user.role,
            full_name=user.full_name,
        )
    )
    return new_access, new_refresh


def revoke_session(db: Session, refresh_token: str) -> None:
    session = (
        db.query(RefreshSession)
        .filter(
            RefreshSession.token_hash == hash_token(refresh_token),
            RefreshSession.revoked.is_(False),
        )
        .first()
    )
    if session:
        session.revoked = True
        db.commit()
