import os

from fastapi import Response


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def attach_auth_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    cookie_secure = _env_bool("COOKIE_SECURE")
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax")
    access_max_age = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15)) * 60
    refresh_max_age = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14)) * 24 * 60 * 60

    response.set_cookie(
        key="app_access",
        value=access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=access_max_age,
    )
    response.set_cookie(
        key="app_refresh",
        value=refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        max_age=refresh_max_age,
    )
