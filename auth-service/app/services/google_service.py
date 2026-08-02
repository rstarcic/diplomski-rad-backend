import os

import aiohttp
from fastapi import status
from errors import raise_auth_error
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
TOKEN_ENDPOINT = os.getenv("TOKEN_ENDPOINT", "https://oauth2.googleapis.com/token")


async def exchange_code_for_tokens(data: dict) -> dict:
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        async with session.post(
            TOKEN_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            if response.status != status.HTTP_200_OK:
                raise_auth_error("token_exchange_failed")
            return await response.json()


def verify_google_token(google_id_token: str) -> dict:
    if not google_id_token:
        raise_auth_error("missing_id_token")
    try:
        return id_token.verify_oauth2_token(
            google_id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
        )
    except GoogleAuthError:
        raise_auth_error("invalid_id_token")


def get_or_raise_google_user(db: Session, claims: dict) -> User:
    user = db.scalar(select(User).where(User.google_sub == claims.get("sub")))
    if user is None:
        raise_auth_error("google_account_not_registered")

    user.profile_picture = claims.get("picture")
    user.full_name = claims.get("name")

    db.commit()
    db.refresh(user)

    return user


def create_google_user(db: Session, claims: dict, role: str) -> User:
    email = claims.get("email")
    google_sub = claims.get("sub")

    if not isinstance(email, str) or not email:
        raise_auth_error("invalid_id_token")

    if not isinstance(google_sub, str) or not google_sub:
        raise_auth_error("invalid_id_token")

    existing_user = db.scalar(select(User).where(User.email == email))

    if existing_user is not None:
        raise_auth_error("email_already_registered")

    user = User(
        email=claims.get("email"),
        google_sub=claims.get("sub"),
        role=role,
        full_name=claims.get("name"),
        profile_picture=claims.get("picture"),
        email_verified=claims.get("email_verified", True),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
