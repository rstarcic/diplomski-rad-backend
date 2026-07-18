from fastapi import HTTPException

CORE_ERRORS = {
    "application_cannot_be_withdrawn": {
        "status_code": 409,
        "code": "application_cannot_be_withdrawn",
        "message": "This application can no longer be withdrawn.",
        "field": "status",
    },
    "job_cannot_be_marked_done": {
        "status_code": 409,
        "code": "job_cannot_be_marked_done",
        "message": "The job cannot be marked done from its current status.",
        "field": "status",
    },
    "job_cannot_be_completed": {
        "status_code": 409,
        "code": "job_cannot_be_completed",
        "message": "Only a job marked done by the contractor can be completed.",
        "field": "status",
    },
    "job_cannot_be_marked_incomplete": {
        "status_code": 409,
        "code": "job_cannot_be_marked_incomplete",
        "message": "Only a job marked done by the contractor can be marked incomplete.",
        "field": "status",
    },
    "contract_status_update_failed": {
        "status_code": 502,
        "code": "contract_status_update_failed",
        "message": "The contract status could not be synchronized.",
        "field": "status",
    },
    "payment_creation_failed": {
        "status_code": 502,
        "code": "payment_creation_failed",
        "message": "The pending payment could not be created.",
        "field": "status",
    },
    "payment_service_timeout": {
        "status_code": 504,
        "code": "payment_service_timeout",
        "message": "The payment service did not respond in time.",
        "field": None,
    },
    "payment_service_unavailable": {
        "status_code": 503,
        "code": "payment_service_unavailable",
        "message": "The payment service is currently unavailable.",
        "field": None,
    },
    "contract_access_forbidden": {
        "status_code": 403,
        "code": "contract_access_forbidden",
        "message": "Only a party to the contract may access it.",
        "field": None,
    },
    "pdf_renderer_unavailable": {
        "status_code": 503,
        "code": "pdf_renderer_unavailable",
        "message": "PDF generation is temporarily unavailable.",
        "field": None,
    },
    "contract_signature_deadline_expired": {
        "status_code": 409,
        "code": "contract_signature_deadline_expired",
        "message": "The contract was not signed by both parties within 24 hours.",
        "field": "status",
    },
    "signature_image_too_large": {
        "status_code": 413,
        "code": "signature_image_too_large",
        "message": "Signature image must not exceed 500 KB.",
        "field": "signature",
    },
    "signature_image_invalid": {
        "status_code": 422,
        "code": "signature_image_invalid",
        "message": "Signature must be a valid Base64-encoded PNG image.",
        "field": "signature",
    },
    "application_not_selected": {
        "status_code": 409,
        "code": "application_not_selected",
        "message": "This application has not been selected.",
        "field": "status",
    },
    "applications_not_found": {
        "status_code": 404,
        "code": "applications_not_found",
        "message": "No applications were found.",
        "field": None,
    },
    "client_not_found": {
        "status_code": 404,
        "code": "client_not_found",
        "message": "The client profile could not be found.",
        "field": "client_id",
    },
    "contractor_not_found": {
        "status_code": 404,
        "code": "contractor_not_found",
        "message": "The contractor profile could not be found.",
        "field": "contractor_id",
    },
    "client_profile_incomplete": {
        "status_code": 409,
        "code": "client_profile_incomplete",
        "message": "The client profile must be completed before creating a contract.",
        "field": "client",
    },
    "contractor_profile_incomplete": {
        "status_code": 409,
        "code": "contractor_profile_incomplete",
        "message": "The contractor profile must be completed before creating a contract.",
        "field": "contractor",
    },
    "contractor_response_required": {
        "status_code": 409,
        "code": "contractor_response_required",
        "message": "The contractor must accept the original job terms.",
        "field": None,
    },
    "not_your_turn": {
        "status_code": 409,
        "code": "not_your_turn",
        "message": "It is not your turn to respond to these terms.",
        "field": "status",
    },
    "negotiation_already_finished": {
        "status_code": 409,
        "code": "negotiation_already_finished",
        "message": "This negotiation has already been completed.",
        "field": "status",
    },
    "negotiation_offer_not_found": {
        "status_code": 404,
        "code": "negotiation_offer_not_found",
        "message": "The latest negotiation offer could not be found.",
        "field": None,
    },
    "contract_creation_failed": {
        "status_code": 502,
        "code": "contract_creation_failed",
        "message": "The contract service failed to create the contract.",
        "field": None,
    },
    "contract_service_timeout": {
        "status_code": 504,
        "code": "contract_service_timeout",
        "message": "The contract service did not respond in time.",
        "field": None,
    },
    "contract_service_unavailable": {
        "status_code": 503,
        "code": "contract_service_unavailable",
        "message": "The contract service is currently unavailable.",
        "field": None,
    },
    "invalid_location_type": {
        "status_code": 422,
        "code": "invalid_location_type",
        "message": "The provided location type is not valid.",
        "field": "location_type",
    },
    "user_not_found": {
        "status_code": 404,
        "code": "user_not_found",
        "message": "The requested user could not be found.",
        "field": "user_id",
    },
    "application_decision_cannot_be_changed": {
        "status_code": 409,
        "code": "application_decision_cannot_be_changed",
        "message": "The decision for this application can no longer be changed.",
        "field": "decision",
    },
    "application_not_found": {
        "status_code": 404,
        "code": "application_not_found",
        "message": "We couldn't find the application you're looking for.",
        "field": None,
    },
    "application_deadline_expired": {
        "status_code": 409,
        "code": "application_deadline_expired",
        "message": "The application deadline for this job has expired.",
        "field": "deadline",
    },
    "application_already_exists": {
        "status_code": 409,
        "code": "application_already_exists",
        "message": "You have already applied for this job.",
        "field": None,
    },
    "job_not_open_for_applications": {
        "status_code": 409,
        "code": "job_not_open_for_applications",
        "message": "This job is no longer accepting applications.",
        "field": "status",
    },
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
    "source_job_not_found": {
        "status_code": 404,
        "code": "source_job_not_found",
        "message": "The source job could not be found.",
        "field": "source_job_id",
    },
    "source_job_forbidden": {
        "status_code": 403,
        "code": "source_job_forbidden",
        "message": "The source job does not belong to the current client.",
        "field": "source_job_id",
    },
    "source_job_not_cancelled": {
        "status_code": 409,
        "code": "source_job_not_cancelled",
        "message": "Only a cancelled job can be replaced.",
        "field": "source_job_id",
    },
    "replacement_job_already_exists": {
        "status_code": 409,
        "code": "replacement_job_already_exists",
        "message": "A replacement for this job already exists.",
        "field": "source_job_id",
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
    "invalid_application_decision": {
        "status_code": 400,
        "code": "invalid_application_decision",
        "message": "The provided application decision is not valid.",
        "field": "decision",
    },
    "negotiation_already_exists": {
        "status_code": 409,
        "code": "negotiation_already_exists",
        "message": "A negotiation already exists for this application.",
        "field": None,
    },
    "negotiation_round_limit_reached": {
        "status_code": 409,
        "code": "negotiation_round_limit_reached",
        "message": "The negotiation ended because the maximum of three rounds was reached.",
        "field": "round_number",
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
