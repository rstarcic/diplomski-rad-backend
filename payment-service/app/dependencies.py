import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Header, Request
from jose import ExpiredSignatureError, JWTError, jwt

from app.payments.schemas import CurrentUser
from errors import raise_payment_error


load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def verify_internal(x_internal_secret: str = Header(...)) -> None:
    if not INTERNAL_SECRET:
        raise_payment_error("internal_authentication_unavailable")
    if not secrets.compare_digest(x_internal_secret, INTERNAL_SECRET):
        raise_payment_error("forbidden")


def _get_access_token_payload(request: Request) -> dict:
    access_token = request.cookies.get("app_access")
    if not access_token:
        raise_payment_error("not_authenticated")
    if not SECRET_KEY:
        raise_payment_error("authentication_unavailable")

    try:
        return jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise_payment_error("token_expired")
    except JWTError:
        raise_payment_error("invalid_token")


def get_current_user_id(request: Request) -> int:
    try:
        return int(_get_access_token_payload(request)["sub"])
    except (KeyError, TypeError, ValueError):
        raise_payment_error("invalid_token")


def get_current_user(request: Request) -> CurrentUser:
    try:
        payload = _get_access_token_payload(request)
        return CurrentUser(
            id=int(payload["sub"]),
            email=str(payload["email"]),
            role=str(payload["role"]),
            full_name=payload.get("full_name"),
        )
    except (KeyError, TypeError, ValueError):
        raise_payment_error("invalid_token")
