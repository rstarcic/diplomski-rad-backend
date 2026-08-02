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


def _split_full_name(full_name: str | None) -> tuple[str | None, str | None]:
    if not full_name:
        return None, None
    parts = full_name.strip().split(maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else None


def _contractor_account_params(
    *,
    user_id: int,
    email: str,
    full_name: str | None,
    product_description: str | None,
    phone: str | None,
    address: str | None,
    postal_code: str | None,
    country_code: str | None,
    city: str | None,
) -> dict:
    first_name, last_name = _split_full_name(full_name)
    normalized_description = (
        " ".join(product_description.split())
        if product_description and product_description.strip()
        else (
            "Freelance professional services provided through the "
            "WorkLink marketplace."
        )
    )
    individual = {"email": email}
    if first_name:
        individual["first_name"] = first_name
    if last_name:
        individual["last_name"] = last_name
    individual_address = {}
    if address:
        individual_address["line1"] = address
    if postal_code:
        individual_address["postal_code"] = postal_code
    if country_code:
        individual_address["country"] = country_code
    if city:
        individual_address["city"] = city
    if individual_address:
        individual["address"] = individual_address

    params = {
        "email": email,
        "business_type": "individual",
        "business_profile": {
            "product_description": normalized_description[:500],
        },
        "individual": individual,
        "capabilities": {
            "transfers": {"requested": True},
        },
        "metadata": {"user_id": str(user_id)},
        "controller": {
            "fees": {"payer": "application"},
            "losses": {"payments": "application"},
            "requirement_collection": "stripe",
            "stripe_dashboard": {"type": "express"},
        },
    }
    if country_code:
        params["country"] = country_code
    return params


def find_connected_account_by_user_id(user_id: int):
    try:
        accounts = stripe_client.v1.accounts.list(params={"limit": 100})
    except stripe.StripeError as exc:
        _log_stripe_error("connected account lookup", exc)
        raise payment_error("stripe_account_creation_failed") from exc

    expected_user_id = str(user_id)
    return next(
        (
            account
            for account in accounts.data
            if account.to_dict().get("metadata", {}).get("user_id")
            == expected_user_id
        ),
        None,
    )


def create_express_connected_account(
    *,
    user_id: int,
    email: str,
    full_name: str | None,
    product_description: str | None,
    phone: str | None,
    address: str | None,
    postal_code: str | None,
    country_code: str | None,
    city: str | None,
):
    params = _contractor_account_params(
        user_id=user_id,
        email=email,
        full_name=full_name,
        product_description=product_description,
        phone=phone,
        address=address,
        postal_code=postal_code,
        country_code=country_code,
        city=city,
    )

    try:
        return stripe_client.v1.accounts.create(
            params=params,
            options={
                "idempotency_key": (
                    f"contractor-connect-account-v1-{user_id}"
                )
            },
        )
    except stripe.StripeError as exc:
        _log_stripe_error("connected account creation", exc)
        raise payment_error("stripe_account_creation_failed") from exc


def update_connected_account_prefill(
    *,
    stripe_account_id: str,
    user_id: int,
    email: str,
    full_name: str | None,
    product_description: str | None,
    phone: str | None,
    address: str | None,
    postal_code: str | None,
    country_code: str | None,
    city: str | None,
):
    params = _contractor_account_params(
        user_id=user_id,
        email=email,
        full_name=full_name,
        product_description=product_description,
        phone=phone,
        address=address,
        postal_code=postal_code,
        country_code=country_code,
        city=city,
    )

    # Stripe collects KYC data for Express accounts. After onboarding has
    # started, the platform can no longer update these identity fields.
    for restricted_field in (
        "business_type",
        "controller",
        "country",
        "email",
        "individual",
    ):
        params.pop(restricted_field, None)

    try:
        return stripe_client.v1.accounts.update(
            stripe_account_id,
            params=params,
        )
    except stripe.StripeError as exc:
        _log_stripe_error("connected account update", exc)
        raise payment_error("stripe_account_creation_failed") from exc


def create_connected_account_link(*, stripe_account_id: str):
    try:
        return stripe_client.v1.account_links.create(
            params={
                "account": stripe_account_id,
                "refresh_url": (
                    f"{FRONTEND_URL}/contractor/settings/"
                    "stripe?connect=refresh"
                ),
                "return_url": (
                    f"{FRONTEND_URL}/contractor/settings/"
                    "stripe?connect=returned"
                ),
                "type": "account_onboarding",
            }
        )
    except stripe.StripeError as exc:
        _log_stripe_error("connected account link creation", exc)
        raise payment_error("stripe_account_link_creation_failed") from exc
