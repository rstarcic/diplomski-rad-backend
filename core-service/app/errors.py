from fastapi import HTTPException

CORE_ERRORS = {
    "profile_not_found": {
        "status_code": 404,
        "code": "profile_not_found",
        "message": "Profile could not be found.",
        "field": None,
    },
    "profile_already_exists": {
        "status_code": 409,
        "code": "profile_already_exists",
        "message": "A profile for this user already exists.",
        "field": None,
    },
    "forbidden": {
        "status_code": 403,
        "code": "forbidden",
        "message": "You do not have permission to perform this action.",
        "field": None,
    },
}


def core_error(error_key: str) -> HTTPException:
    error = CORE_ERRORS[error_key]
    return HTTPException(
        status_code=error["status_code"],
        detail={
            "code": error["code"],
            "message": error["message"],
            "field": error["field"],
        },
    )


def raise_core_error(error_key: str) -> None:
    raise core_error(error_key)
