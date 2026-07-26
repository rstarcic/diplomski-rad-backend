import os

import stripe
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_current_user_id
from app.integrations.stripe_client import stripe_client
from app.models import JobPayment, PaymentProfile
from app.payments.schemas import (
    CheckoutSessionResponse,
    ConnectOnboardingRequest,
    ConnectOnboardingResponse,
    CurrentUser,
    PaymentSetupRequest,
    PaymentStatusResponse,
)
from app.payments.service import (
    complete_payment_setup,
    create_contract_checkout_session,
    create_contractor_connect_onboarding,
    create_payment_method_setup_session,
    get_payment_profile,
    sync_connected_account_status,
)
from database import get_db
from errors import raise_payment_error

router = APIRouter(prefix="/payments", tags=["payments"])
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@router.get("/status", response_model=PaymentStatusResponse)
def get_my_payment_status(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = get_payment_profile(db, current_user_id)
    if profile is None:
        raise_payment_error("payment_profile_not_found")
    return profile


@router.post(
    "/setup-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_method_setup_session_endpoint(
    data: PaymentSetupRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutSessionResponse:
    if current_user.role != "client":
        raise_payment_error("forbidden")
    checkout_url = create_payment_method_setup_session(
        db=db,
        current_user=current_user,
        data=data,
    )

    return CheckoutSessionResponse(
        checkout_url=checkout_url,
    )


@router.post(
    "/connect/onboarding",
    response_model=ConnectOnboardingResponse,
)
async def create_connect_onboarding_endpoint(
    data: ConnectOnboardingRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    onboarding_url = await create_contractor_connect_onboarding(
        db=db,
        current_user=current_user,
        data=data,
    )
    return ConnectOnboardingResponse(onboarding_url=onboarding_url)
@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook_endpoint(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    if not STRIPE_WEBHOOK_SECRET:
        raise_payment_error("stripe_webhook_unavailable")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise_payment_error("invalid_webhook_payload")
    except stripe.SignatureVerificationError:
        raise_payment_error("invalid_webhook_signature")

    event_type = event.type
    stripe_object = event.data.object

    def metadata_value(metadata, key: str):
        if not metadata:
            return None

        if isinstance(metadata, dict):
            return metadata.get(key)

        return getattr(metadata, key, None)

    def commit() -> None:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    def find_job_payment(
        *,
        payment_intent_id: str | None = None,
        metadata=None,
    ) -> JobPayment | None:
        payment_id = metadata_value(metadata, "payment_id")

        if payment_id:
            try:
                return db.get(JobPayment, int(payment_id))
            except (TypeError, ValueError):
                raise_payment_error("invalid_webhook_payload")

        if payment_intent_id:
            return (
                db.query(JobPayment)
                .filter(
                    JobPayment.stripe_payment_intent_id
                    == payment_intent_id
                )
                .first()
            )

        return None

    def validate_payment(
        payment: JobPayment,
        *,
        amount: int | None,
        currency: str | None,
    ) -> None:
        if amount is not None and amount != payment.amount_minor:
            raise_payment_error("payment_amount_mismatch")

        if (
            currency
            and currency.lower() != payment.currency.lower()
        ):
            raise_payment_error("payment_amount_mismatch")

    def clear_payment_method(profile: PaymentProfile) -> None:
        profile.payment_setup_completed = False
        profile.stripe_payment_method_id = None
        profile.card_brand = None
        profile.card_last4 = None
        profile.card_exp_month = None
        profile.card_exp_year = None

    # ------------------------------------------------------------------
    # Stripe Connect onboarding
    # ------------------------------------------------------------------

    if event_type == "account.updated":
        account = stripe_object

        sync_connected_account_status(
            db,
            {
                "id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
            },
        )

        return {"received": True}

    # ------------------------------------------------------------------
    # Checkout Session
    # ------------------------------------------------------------------

    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed",
        "checkout.session.expired",
    }:
        session = stripe_object
        metadata = session.metadata

        # ----------------------- Setup Checkout -----------------------

        if (
            session.mode == "setup"
            and metadata_value(metadata, "purpose") == "payment_setup"
        ):
            try:
                user_id = int(metadata_value(metadata, "user_id"))
            except (TypeError, ValueError):
                raise_payment_error("invalid_webhook_payload")

            profile = get_payment_profile(db, user_id)

            if profile is None:
                raise_payment_error("invalid_webhook_payload")

            if (
                session.customer
                and profile.stripe_customer_id != str(session.customer)
            ):
                raise_payment_error("invalid_webhook_payload")

            if event_type == "checkout.session.expired":
                profile.payment_setup_completed = False
                commit()
                return {"received": True}

            setup_intent_id = (
                str(session.setup_intent)
                if session.setup_intent
                else None
            )

            if not setup_intent_id:
                profile.payment_setup_completed = False
                commit()
                return {"received": True}

            setup_intent = stripe_client.v1.setup_intents.retrieve(
                setup_intent_id
            )

            if setup_intent.status != "succeeded":
                profile.payment_setup_completed = False
                commit()
                return {"received": True}

            payment_method_data = None

            if setup_intent.payment_method:
                payment_method = (
                    stripe_client.v1.payment_methods.retrieve(
                        str(setup_intent.payment_method)
                    )
                )

                card = getattr(payment_method, "card", None)

                payment_method_data = {
                    "id": payment_method.id,
                    "card": {
                        "brand": getattr(card, "brand", None),
                        "last4": getattr(card, "last4", None),
                        "exp_month": getattr(card, "exp_month", None),
                        "exp_year": getattr(card, "exp_year", None),
                    },
                }

            billing_address = None
            customer_details = session.customer_details

            if customer_details and customer_details.address:
                address = customer_details.address

                billing_address = {
                    "line1": address.line1 or "",
                    "postal_code": address.postal_code or "",
                    "country": address.country or "",
                }

            complete_payment_setup(
                db=db,
                user_id=user_id,
                stripe_customer_id=str(session.customer),
                payment_method=payment_method_data,
                billing_address=billing_address,
            )

            return {"received": True}

        # ---------------------- Payment Checkout ----------------------

        if session.mode == "payment":
            try:
                payment_id = int(
                    metadata_value(metadata, "payment_id")
                )
                contract_id = int(
                    metadata_value(metadata, "contract_id")
                )
                application_id = int(
                    metadata_value(metadata, "application_id")
                )
            except (TypeError, ValueError):
                raise_payment_error("invalid_webhook_payload")

            payment = db.get(JobPayment, payment_id)

            if payment is None:
                raise_payment_error("payment_not_found")

            if (
                payment.stripe_checkout_session_id != session.id
                or payment.contract_id != contract_id
                or payment.application_id != application_id
            ):
                raise_payment_error("invalid_webhook_payload")

            validate_payment(
                payment,
                amount=session.amount_total,
                currency=session.currency,
            )

            if session.payment_intent:
                payment.stripe_payment_intent_id = str(
                    session.payment_intent
                )

            if event_type in {
                "checkout.session.completed",
                "checkout.session.async_payment_succeeded",
            }:
                # Za async metode completed može doći dok je još unpaid.
                payment.status = (
                    "paid"
                    if session.payment_status == "paid"
                    else "pending"
                )

            elif event_type == "checkout.session.async_payment_failed":
                # Korisnik može ponovno pokušati platiti.
                payment.status = "pending"

            elif event_type == "checkout.session.expired":
                if payment.status != "paid":
                    payment.status = "cancelled"

            commit()
            return {"received": True}

    # ------------------------------------------------------------------
    # PaymentIntent
    # ------------------------------------------------------------------

    if event_type.startswith("payment_intent."):
        payment_intent = stripe_object

        payment = find_job_payment(
            payment_intent_id=payment_intent.id,
            metadata=payment_intent.metadata,
        )

        # Može pripadati nekom drugom Stripe toku.
        if payment is None:
            return {"received": True}

        validate_payment(
            payment,
            amount=getattr(payment_intent, "amount", None),
            currency=getattr(payment_intent, "currency", None),
        )

        payment.stripe_payment_intent_id = payment_intent.id
        intent_status = payment_intent.status

        if intent_status == "succeeded":
            payment.status = "paid"

        elif intent_status == "canceled":
            if payment.status != "paid":
                payment.status = "cancelled"

        elif intent_status in {
            "requires_payment_method",
            "requires_confirmation",
            "requires_action",
            "processing",
            "requires_capture",
        }:
            if payment.status != "paid":
                payment.status = "pending"

        commit()
        return {"received": True}

    # ------------------------------------------------------------------
    # SetupIntent
    # ------------------------------------------------------------------

    if event_type.startswith("setup_intent."):
        setup_intent = stripe_object

        if not setup_intent.customer:
            return {"received": True}

        profile = (
            db.query(PaymentProfile)
            .filter(
                PaymentProfile.stripe_customer_id
                == str(setup_intent.customer)
            )
            .first()
        )

        if profile is None:
            return {"received": True}

        if setup_intent.status == "succeeded":
            payment_method = None

            if setup_intent.payment_method:
                payment_method = (
                    stripe_client.v1.payment_methods.retrieve(
                        str(setup_intent.payment_method)
                    )
                )

            profile.payment_setup_completed = True

            if payment_method:
                profile.stripe_payment_method_id = payment_method.id

                card = getattr(payment_method, "card", None)

                if card:
                    profile.card_brand = card.brand
                    profile.card_last4 = card.last4
                    profile.card_exp_month = card.exp_month
                    profile.card_exp_year = card.exp_year

        elif setup_intent.status == "canceled":
            clear_payment_method(profile)

        elif setup_intent.status in {
            "requires_payment_method",
            "requires_confirmation",
            "requires_action",
            "processing",
        }:
            profile.payment_setup_completed = False

        commit()
        return {"received": True}

    return {"received": True}

@router.post(
    "/contracts/{contract_id}/checkout-session",
    response_model=CheckoutSessionResponse,
)
async def create_checkout_session_endpoint(
    contract_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    checkout_url = await create_contract_checkout_session(
        db=db,
        contract_id=contract_id,
        current_user_id=current_user_id,
    )
    return CheckoutSessionResponse(checkout_url=checkout_url)
