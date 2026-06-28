import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from app.schemas import TokenPayload
from errors import raise_auth_error
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 15

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(
    payload: TokenPayload,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
) -> str:
    data = payload.model_dump()
    data["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise_auth_error("token_expired")
    except JWTError:
        raise_auth_error("invalid_token")


def generate_refresh_token():
    return secrets.token_urlsafe(32)


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()
