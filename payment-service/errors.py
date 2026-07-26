from fastapi import HTTPException

PAYMENT_ERRORS = {
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
    "invalid_token": {
        "status_code": 401,
        "code": "invalid_token",
        "message": "Your session is no longer valid. Please log in again.",
        "field": None,
    },
    "authentication_unavailable": {
        "status_code": 503,
        "code": "authentication_unavailable",
        "message": "Authentication is not configured.",
        "field": None,
    },
    "internal_authentication_unavailable": {
        "status_code": 503,
        "code": "internal_authentication_unavailable",
        "message": "Internal API authentication is not configured.",
        "field": None,
    },
    "forbidden": {
        "status_code": 403,
        "code": "forbidden",
        "message": "You do not have permission to perform this action.",
        "field": None,
    },
    "only_clients_can_pay": {
        "status_code": 403,
        "code": "only_clients_can_pay",
        "message": "Only the contract client can make this payment.",
        "field": None,
    },
    "only_contractors_can_connect": {
        "status_code": 403,
        "code": "only_contractors_can_connect",
        "message": "Only contractors can configure Stripe payouts.",
        "field": None,
    },
    "payment_profile_not_found": {
        "status_code": 404,
        "code": "payment_profile_not_found",
        "message": "The payment profile could not be found.",
        "field": None,
    },
    "payment_not_found": {
        "status_code": 404,
        "code": "payment_not_found",
        "message": "The payment could not be found.",
        "field": None,
    },
    "payment_amount_mismatch": {
        "status_code": 409,
        "code": "payment_amount_mismatch",
        "message": "The completed payment does not match the expected amount.",
        "field": "amount",
    },
    "contractor_profile_not_found": {
        "status_code": 404,
        "code": "contractor_profile_not_found",
        "message": "The contractor profile could not be found.",
        "field": None,
    },
    "contract_not_found": {
        "status_code": 404,
        "code": "contract_not_found",
        "message": "The contract could not be found.",
        "field": "contract_id",
    },
    "contract_not_payable": {
        "status_code": 409,
        "code": "contract_not_payable",
        "message": "The contract is not ready for payment.",
        "field": "status",
    },
    "payment_already_paid": {
        "status_code": 409,
        "code": "payment_already_paid",
        "message": "This contract has already been paid.",
        "field": "status",
    },
    "contract_service_failed": {
        "status_code": 502,
        "code": "contract_service_failed",
        "message": "The contract service could not process the request.",
        "field": None,
    },
    "contract_service_unavailable": {
        "status_code": 503,
        "code": "contract_service_unavailable",
        "message": "The contract service is currently unavailable.",
        "field": None,
    },
    "contract_service_timeout": {
        "status_code": 504,
        "code": "contract_service_timeout",
        "message": "The contract service did not respond in time.",
        "field": None,
    },
    "core_service_failed": {
        "status_code": 502,
        "code": "core_service_failed",
        "message": "The core service could not process the request.",
        "field": None,
    },
    "core_service_unavailable": {
        "status_code": 503,
        "code": "core_service_unavailable",
        "message": "The core service is currently unavailable.",
        "field": None,
    },
    "core_service_timeout": {
        "status_code": 504,
        "code": "core_service_timeout",
        "message": "The core service did not respond in time.",
        "field": None,
    },
    "stripe_account_creation_failed": {
        "status_code": 502,
        "code": "stripe_account_creation_failed",
        "message": "The Stripe connected account could not be created.",
        "field": None,
    },
    "stripe_account_link_creation_failed": {
        "status_code": 502,
        "code": "stripe_account_link_creation_failed",
        "message": "The Stripe onboarding link could not be created.",
        "field": None,
    },
    "stripe_customer_creation_failed": {
        "status_code": 502,
        "code": "stripe_customer_creation_failed",
        "message": "The Stripe customer could not be created.",
        "field": None,
    },
    "stripe_customer_update_failed": {
        "status_code": 502,
        "code": "stripe_customer_update_failed",
        "message": "The Stripe customer could not be updated.",
        "field": None,
    },
    "checkout_session_creation_failed": {
        "status_code": 502,
        "code": "checkout_session_creation_failed",
        "message": "The checkout session could not be created.",
        "field": None,
    },
    "setup_session_creation_failed": {
        "status_code": 502,
        "code": "setup_session_creation_failed",
        "message": "The payment setup session could not be created.",
        "field": None,
    },
    "checkout_session_url_missing": {
        "status_code": 502,
        "code": "checkout_session_url_missing",
        "message": "The checkout session URL was not returned by Stripe.",
        "field": None,
    },
    "stripe_webhook_unavailable": {
        "status_code": 503,
        "code": "stripe_webhook_unavailable",
        "message": "Stripe webhook verification is not configured.",
        "field": None,
    },
    "invalid_webhook_signature": {
        "status_code": 400,
        "code": "invalid_webhook_signature",
        "message": "The Stripe webhook signature is invalid.",
        "field": None,
    },
    "invalid_webhook_payload": {
        "status_code": 400,
        "code": "invalid_webhook_payload",
        "message": "The Stripe webhook payload is invalid.",
        "field": None,
    },
}


def payment_error(error_key: str) -> HTTPException:
    error = PAYMENT_ERRORS[error_key]
    return HTTPException(
        status_code=error["status_code"],
        detail={
            "code": error["code"],
            "message": error["message"],
            "field": error["field"],
        },
    )


def raise_payment_error(error_key: str) -> None:
    raise payment_error(error_key)
