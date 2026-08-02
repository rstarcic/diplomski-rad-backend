import os
import secrets
from pathlib import Path

from app.profiles.models import Profile
from database import get_db
from dotenv import load_dotenv
from errors import raise_core_error
from fastapi import Depends, Header, HTTPException, Request, status
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _verify_internal(x_internal_secret: str = Header(...)) -> None:
    if not INTERNAL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API authentication is not configured.",
        )
    if not secrets.compare_digest(x_internal_secret, INTERNAL_SECRET):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )


def decode_access_token(token: str) -> dict:
    if not SECRET_KEY:
        raise_core_error("invalid_token")

    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise_core_error("token_expired")
    except JWTError:
        raise_core_error("invalid_token")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Profile:
    access_token = request.cookies.get("app_access")
    if not access_token:
        raise_core_error("not_authenticated")

    payload = decode_access_token(access_token)
    user_id = payload.get("sub")
    if not user_id:
        raise_core_error("invalid_or_expired_token")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise_core_error("invalid_or_expired_token")

    profile = db.scalars(select(Profile).where(Profile.user_id == user_id)).first()
    if not profile:
        raise_core_error("profile_not_found")

    return profile
