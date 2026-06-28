import secrets
from datetime import datetime, timedelta, timezone

from app.models import PasswordResetToken, User
from app.utils.security import hash_password, hash_token
from errors import raise_auth_error
from sqlalchemy.orm import Session


def request_password_reset(
    db: Session, email: str
) -> tuple[str, str | None] | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash:
        return None

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used.is_(False),
    ).delete()

    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
    )
    db.commit()
    return raw_token, user.full_name


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == hash_token(raw_token),
            PasswordResetToken.used.is_(False),
        )
        .first()
    )

    if not record or record.expires_at < datetime.now(timezone.utc):
        raise_auth_error("reset_token_invalid")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise_auth_error("user_not_found")

    user.password_hash = hash_password(new_password)
    record.used = True
    db.commit()
