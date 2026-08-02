import secrets
from datetime import UTC, datetime, timedelta

from errors import raise_auth_error
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import EmailVerificationToken, User
from app.utils.security import hash_token


def create_verification_token(
    db: Session,
    user_id: int,
) -> str:
    db.execute(
        delete(EmailVerificationToken).where(EmailVerificationToken.user_id == user_id)
    )

    raw_token = secrets.token_urlsafe(32)

    verification_token = EmailVerificationToken(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )

    db.add(verification_token)
    db.commit()

    return raw_token


def verify_email_token(db: Session, raw_token: str) -> None:
    record = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_token(raw_token)
        )
    )

    if record is None or record.expires_at < datetime.now(UTC):
        raise_auth_error("email_link_expired")

    user = db.scalars(select(User).where(User.id == record.user_id)).first()
    if user is None:
        raise_auth_error("user_not_found")

    user.email_verified = True
    db.delete(record)
    db.commit()
