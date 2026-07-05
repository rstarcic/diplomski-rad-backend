from fastapi import HTTPException

CORE_ERRORS = {
    "only_clients_can_update_jobs": {
        "status_code": 403,
        "code": "only_clients_can_update_jobs",
        "message": "Only clients can update jobs.",
        "field": None,
    },
    "job_not_found": {
        "status_code": 404,
        "code": "job_not_found",
        "message": "We couldn't find the job you're looking for.",
        "field": None,
    },
    "job_failed_to_create": {
        "status_code": 500,
        "code": "job_failed_to_create",
        "message": "Failed to create the job. Please try again later.",
        "field": None,
    },
    "job_cannot_be_updated": {
        "status_code": 409,
        "code": "job_cannot_be_updated",
        "message": "Only open jobs can be updated.",
        "field": "status",
    },
    "profile_picture_invalid_type": {
        "status_code": 422,
        "code": "profile_picture_invalid_type",
        "message": "Profile picture must be an image.",
        "field": "profile_picture",
    },
    "profile_picture_empty": {
        "status_code": 422,
        "code": "profile_picture_empty",
        "message": "Profile picture cannot be empty.",
        "field": "profile_picture",
    },
    "invalid_multipart_json": {
        "status_code": 422,
        "code": "invalid_multipart_json",
        "message": "Invalid JSON in multipart field.",
        "field": None,
    },
    "profile_not_found": {
        "status_code": 404,
        "code": "profile_not_found",
        "message": "We couldn't find your profile.",
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
    "not_authenticated": {
        "status_code": 401,
        "code": "not_authenticated",
        "message": "You must be logged in to access this resource.",
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
