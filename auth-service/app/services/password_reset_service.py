import secrets
from datetime import UTC, datetime, timedelta

from errors import raise_auth_error
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import PasswordResetToken, User
from app.utils.security import hash_password, hash_token


def request_password_reset(db: Session, email: str) -> tuple[str, str | None] | None:
    user = db.scalar(select(User).where(User.email == email))

    if user is None or user.password_hash is None:
        return None

    db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
        )
    )

    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(minutes=15),
        )
    )
    db.commit()
    return raw_token, user.full_name


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    record = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == hash_token(raw_token),
            PasswordResetToken.used.is_(False),
        )
        .with_for_update()
    )

    if record is None or record.expires_at < datetime.now(UTC):
        raise_auth_error("reset_token_invalid")

    user = db.get(User, record.user_id)

    if user is None:
        raise_auth_error("user_not_found")

    user.password_hash = hash_password(new_password)
    record.used = True
    db.commit()
