import logging
import os

import stripe

from app.integrations.stripe_client import stripe_client
from errors import payment_error

logger = logging.getLogger(__name__)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def _log_stripe_error(operation: str, exc: stripe.StripeError) -> None:
    logger.error(
        "Stripe %s failed: type=%s code=%s message=%s",
        operation,
        type(exc).__name__,
        getattr(exc, "code", None),
        getattr(exc, "user_message", None) or str(exc),
    )


def create_stripe_customer(
    *,
    user_id: int,
    name: str | None,
    email: str,
    address: dict | None = None,
):
    params = {
        "name": name,
        "email": email,
        "metadata": {
            "user_id": str(user_id),
        },
    }
    if address is not None:
        params["address"] = address

    try:
        return stripe_client.v1.customers.create(
            params=params,
            options={
                "idempotency_key": f"stripe-customer-client{user_id}",
            },
        )
    except stripe.StripeError as exc:
        _log_stripe_error("customer creation", exc)
        raise payment_error("stripe_customer_creation_failed") from exc


def update_stripe_customer(
    *,
    stripe_customer_id: str,
    address: dict,
    name: str | None = None,
    email: str | None = None,
):
    params = {"address": address}
    if name is not None:
        params["name"] = name
    if email is not None:
        params["email"] = email
    try:
        return stripe_client.v1.customers.update(
            stripe_customer_id,
            params=params,
        )
    except stripe.StripeError as exc:
        _log_stripe_error("customer update", exc)
        raise payment_error("stripe_customer_update_failed") from exc


def create_checkout_session(
    *,
    payment,
    stripe_customer_id: str,
    contractor_stripe_account_id: str,
):
    attempt = payment.checkout_attempt + 1
    application_url = (
        f"{FRONTEND_URL}/client/jobs/{payment.job_id}"
        f"/applications/{payment.application_id}"
    )
    try:
        return stripe_client.v1.checkout.sessions.create(
            params={
                "customer": stripe_customer_id,
                "mode": "payment",
                "client_reference_id": str(payment.id),
                "line_items": [
                    {
                        "price_data": {
                            "currency": payment.currency.lower(),
                            "product_data": {"name": payment.job_title},
                            "unit_amount": payment.amount_minor,
                        },
                        "quantity": 1,
                    }
                ],
                "payment_intent_data": {
                    "transfer_data": {
                        "destination": contractor_stripe_account_id,
                    },
                    "description": f"Payment for job: {payment.job_title}",
                    "metadata": {
                        "payment_id": str(payment.id),
                        "contract_id": str(payment.contract_id),
                        "application_id": str(payment.application_id),
                        "job_id": str(payment.job_id),
                        "job_title": payment.job_title,
                    },
                },
                "success_url": (
                    f"{application_url}"
                    "?payment=success"
                    "&session_id={{CHECKOUT_SESSION_ID}}"
                ),
                "cancel_url": (f"{application_url}" "?payment=cancelled"),
                "metadata": {
                    "payment_id": str(payment.id),
                    "contract_id": str(payment.contract_id),
                    "application_id": str(payment.application_id),
                    "job_id": str(payment.job_id),
                },
            },
            options={
                "idempotency_key": (
                    f"checkout-payment-{payment.id}-attempt-{attempt}"
                )
            },
        )
    except stripe.StripeError as exc:
        _log_stripe_error("checkout session creation", exc)
        raise payment_error("checkout_session_creation_failed") from exc


def create_payment_setup_session(
    *,
    user_id: int,
    stripe_customer_id: str,
):
    try:
        return stripe_client.v1.checkout.sessions.create(
            params={
                "customer": stripe_customer_id,
                "mode": "setup",
                "payment_method_types": ["card"],
                "success_url": (
                    f"{FRONTEND_URL}/client/settings/stripe"
                    "?setup=success"
                    "&session_id={{CHECKOUT_SESSION_ID}}"
                ),
                "cancel_url": (
                    f"{FRONTEND_URL}/client/settings/stripe" "?setup=cancelled"
                ),
                "metadata": {
                    "purpose": "payment_setup",
                    "user_id": str(user_id),
                },
            }
        )
    except stripe.StripeError as exc:
        _log_stripe_error("setup session creation", exc)
        raise payment_error("setup_session_creation_failed") from exc

