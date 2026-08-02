import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta, timezone

from errors import raise_auth_error
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import OAuthPKCE


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_pkce_session(db: Session, flow_type: str) -> tuple[str, str]:
    now = datetime.now(UTC)
    db.execute(delete(OAuthPKCE).where(OAuthPKCE.expires_at < now))

    state = secrets.token_urlsafe(32)
    verifier = _base64url(secrets.token_bytes(32))
    challenge = _base64url(hashlib.sha256(verifier.encode()).digest())

    pkce_session = OAuthPKCE(
        state=state,
        code_verifier=verifier,
        expires_at=now + timedelta(minutes=10),
        flow_type=flow_type,
    )

    db.add(pkce_session)
    db.commit()
    return state, challenge


def consume_pkce_session(db: Session, state: str) -> tuple[str, str]:
    pkce = db.scalars(
        select(OAuthPKCE).where(OAuthPKCE.state == state).with_for_update()
    ).one_or_none()

    if pkce is None:
        raise_auth_error("invalid_state")

    if pkce.expires_at < datetime.now(UTC):
        db.delete(pkce)
        db.commit()
        raise_auth_error("state_expired")

    verifier, flow_type = pkce.code_verifier, pkce.flow_type
    db.delete(pkce)
    db.commit()

    return verifier, flow_type
