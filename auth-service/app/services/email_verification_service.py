import secrets
from datetime import datetime, timedelta, timezone

from app.models import EmailVerificationToken, User
from app.utils.security import hash_token
from errors import raise_auth_error
from sqlalchemy.orm import Session


def create_verification_token(db: Session, user_id: int) -> str:
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user_id,
    ).delete()

    raw_token = secrets.token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
    )
    db.commit()
    return raw_token


def verify_email_token(db: Session, raw_token: str) -> None:
    record = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.token_hash == hash_token(raw_token),
        )
        .first()
    )

    if not record or record.expires_at < datetime.now(timezone.utc):
        raise_auth_error("email_link_expired")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise_auth_error("user_not_found")

    user.email_verified = True
    db.delete(record)
    db.commit()
