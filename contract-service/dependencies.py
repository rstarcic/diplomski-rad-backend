import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Request
from jose import ExpiredSignatureError, JWTError, jwt

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def _auth_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "field": None},
    )


def get_current_user_id(request: Request) -> int:
    access_token = request.cookies.get("app_access")
    if not access_token:
        _auth_error(401, "not_authenticated", "Authentication is required.")
    if not SECRET_KEY:
        _auth_error(503, "authentication_unavailable", "Authentication is not configured.")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        _auth_error(401, "token_expired", "The access token has expired.")
    except JWTError:
        _auth_error(401, "invalid_token", "The access token is invalid.")

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        _auth_error(401, "invalid_token", "The access token is invalid.")

