from collections.abc import Mapping
from typing import Any, Never

from fastapi import HTTPException, status

AUTH_ERRORS = {
    "invalid_credentials": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "invalid_credentials",
        "message": "Email or password is incorrect.",
        "field": None,
    },
    "not_authenticated": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "not_authenticated",
        "message": "You must be logged in to access this resource.",
        "field": None,
    },
    "google_account_not_registered": {
        "status_code": status.HTTP_404_NOT_FOUND,
        "code": "google_account_not_registered",
        "message": (
            "This Google account is not registered yet. "
            "Please complete registration first."
        ),
        "field": None,
    },
    "email_already_registered": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "email_already_registered",
        "message": "An account with this email already exists.",
        "field": "email",
    },
    "invalid_role": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "invalid_role",
        "message": "The selected role is invalid.",
        "field": "role",
    },
    "invalid_state": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "invalid_state",
        "message": "Authentication could not be completed. Please try again.",
        "field": None,
    },
    "state_expired": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "state_expired",
        "message": "Authentication session has expired. Please try again.",
        "field": None,
    },
    "missing_code_or_state": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "missing_code_or_state",
        "message": ("Google authentication response is incomplete. Please try again."),
        "field": None,
    },
    "token_exchange_failed": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "token_exchange_failed",
        "message": "Google authentication failed. Please try again later.",
        "field": None,
    },
    "invalid_id_token": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "invalid_id_token",
        "message": "Google authentication failed. Please try again.",
        "field": None,
    },
    "token_expired": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "token_expired",
        "message": "Your session has expired. Please log in again.",
        "field": None,
    },
    "invalid_or_expired_token": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "invalid_or_expired_token",
        "message": "Your session is no longer valid. Please log in again.",
        "field": None,
    },
    "invalid_token": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "invalid_token",
        "message": "Your session is no longer valid. Please log in again.",
        "field": None,
    },
    "missing_id_token": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "missing_id_token",
        "message": "Google authentication failed. Please try again.",
        "field": None,
    },
    "user_not_found": {
        "status_code": status.HTTP_404_NOT_FOUND,
        "code": "user_not_found",
        "message": "User account could not be found.",
        "field": None,
    },
    "google_oauth_cancelled": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "google_oauth_cancelled",
        "message": "Google sign-in was cancelled.",
        "field": None,
    },
    "refresh_token_expired": {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "refresh_token_expired",
        "message": "Your session has expired. Please log in again.",
        "field": None,
    },
    "account_not_verified": {
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "account_not_verified",
        "message": ("Please verify your email address before logging in."),
        "field": None,
    },
    "email_link_expired": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "email_link_expired",
        "message": "This verification link has expired. Please request a new one.",
        "field": None,
    },
    "reset_token_invalid": {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "code": "reset_token_invalid",
        "message": "This reset link is invalid or has expired. Please request a new one.",
        "field": None,
    },
    "email_send_failed": {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "code": "email_send_failed",
        "message": "We couldn't send the reset email. Please try again later.",
        "field": None,
    },
}


def auth_error(error_key: str) -> HTTPException:
    error = AUTH_ERRORS[error_key]

    return HTTPException(
        status_code=error["status_code"],
        detail={
            "code": error["code"],
            "message": error["message"],
            "field": error["field"],
        },
    )


def raise_auth_error(error_key: str) -> Never:
    raise auth_error(error_key)


def get_error_code(detail: Any) -> str:
    if isinstance(detail, Mapping):
        code = detail.get("code")

        if isinstance(code, str):
            return code

    return "unknown_error"

