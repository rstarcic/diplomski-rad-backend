import os
from datetime import datetime, timedelta, timezone

from errors import raise_auth_error
from jose import ExpiredSignatureError, JWTError, jwt

from app.schemas import TokenPayload

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))


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
