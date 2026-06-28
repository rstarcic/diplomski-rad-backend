from fastapi import HTTPException

AUTH_ERRORS = {
    "invalid_credentials": {
        "status_code": 401,
        "code": "invalid_credentials",
        "message": "Email or password is incorrect.",
        "field": None,
    },
    "not_authenticated": {
        "status_code": 401,
        "code": "not_authenticated",
        "message": "You must be logged in to access this resource.",
        "field": None,
    },
    "google_account_not_registered": {
        "status_code": 404,
        "code": "google_account_not_registered",
        "message": "This Google account is not registered yet. Please complete registration first.",
        "field": None,
    },
    "email_already_registered": {
        "status_code": 400,
        "code": "email_already_registered",
        "message": "An account with this email already exists.",
        "field": "email",
    },
    "invalid_role": {
        "status_code": 400,
        "code": "invalid_role",
        "message": "The selected role is invalid.",
        "field": "role",
    },
    "invalid_state": {
        "status_code": 400,
        "code": "invalid_state",
        "message": "Authentication could not be completed. Please try again.",
        "field": None,
    },
    "state_expired": {
        "status_code": 400,
        "code": "state_expired",
        "message": "Authentication session has expired. Please try again.",
        "field": None,
    },
    "missing_code_or_state": {
        "status_code": 400,
        "code": "missing_code_or_state",
        "message": "Google authentication response is incomplete. Please try again.",
        "field": None,
    },
    "token_exchange_failed": {
        "status_code": 400,
        "code": "token_exchange_failed",
        "message": "Google authentication failed. Please try again later.",
        "field": None,
    },
    "invalid_id_token": {
        "status_code": 401,
        "code": "invalid_id_token",
        "message": "Google authentication failed. Please try again.",
        "field": None,
    },
    "token_expired": {
        "status_code": 401,
        "code": "token_expired",
        "message": "Your session has expired. Please log in again.",
        "field": None,
    },
    "invalid_or_expired_token": {
        "status_code": 401,
        "code": "invalid_or_expired_token",
        "message": "Your session is no longer valid. Please log in again.",
        "field": None,
    },
    "invalid_token": {
        "status_code": 401,
        "code": "invalid_token",
        "message": "Your session is no longer valid. Please log in again.",
        "field": None,
    },
    "missing_id_token": {
        "status_code": 400,
        "code": "missing_id_token",
        "message": "Google authentication failed. Please try again.",
        "field": None,
    },
    "user_not_found": {
        "status_code": 404,
        "code": "user_not_found",
        "message": "User account could not be found.",
        "field": None,
    },
    "google_oauth_cancelled": {
        "status_code": 400,
        "code": "google_oauth_cancelled",
        "message": "Google sign-in was cancelled.",
        "field": None,
    },
    "refresh_token_expired": {
        "status_code": 401,
        "code": "refresh_token_expired",
        "message": "Your session has expired. Please log in again.",
        "field": None,
    },
    "reset_token_invalid": {
        "status_code": 400,
        "code": "reset_token_invalid",
        "message": "This reset link is invalid or has expired. Please request a new one.",
        "field": None,
    },
    "email_send_failed": {
        "status_code": 500,
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


def raise_auth_error(error_key: str) -> None:
    raise auth_error(error_key)


def get_error_code(detail) -> str:
    if isinstance(detail, dict):
        return detail.get("code", "unknown_error")
    return "unknown_error"
