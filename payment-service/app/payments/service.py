import logging
from datetime import datetime, timedelta, timezone

from app.integrations.contract_client import get_contract_payment_details
from app.integrations.core_client import get_contractor_profile
from app.integrations.stripe_checkout import (
    create_checkout_session,
    create_payment_setup_session,
    create_stripe_customer,
    update_stripe_customer,
)
from app.integrations.stripe_connect import (
    create_connected_account_link,
    create_express_connected_account,
    find_connected_account_by_user_id,
    update_connected_account_prefill,
)
from app.models import JobPayment, PaymentProfile
from app.payments.schemas import CurrentUser, PaymentSetupRequest, ConnectOnboardingRequest
from errors import raise_payment_error
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_payment_profile(db: Session, user_id: int) -> PaymentProfile | None:
    return db.query(PaymentProfile).filter(PaymentProfile.user_id == user_id).first()


def get_or_create_client_payment_profile(
    db: Session,
    user_id: int,
) -> PaymentProfile:
    profile = get_payment_profile(db, user_id)

    if profile:
        if profile.role != "client":
            raise_payment_error("only_clients_can_pay")
        return profile

    profile = PaymentProfile(
        user_id=user_id,
        role="client",
    )
    db.add(profile)
    db.flush()

    return profile


def get_or_create_contractor_payment_profile(
    db: Session,
    user_id: int,
) -> PaymentProfile:
    profile = get_payment_profile(db, user_id)

    if profile:
        if profile.role != "contractor":
            raise_payment_error("only_contractors_can_connect")
        return profile

    profile = PaymentProfile(user_id=user_id, role="contractor")
    db.add(profile)
    db.flush()
    return profile

async def create_contractor_connect_onboarding(
    *,
    db: Session,
    current_user: CurrentUser,
    data: ConnectOnboardingRequest,
) -> str:
    if current_user.role != "contractor":
        raise_payment_error("only_contractors_can_connect")

    contractor = await get_contractor_profile(current_user.id)
    payment_profile = get_or_create_contractor_payment_profile(
        db,
        current_user.id,
    )
    payment_profile.billing_address = data.address.strip()
    payment_profile.billing_postal_code = data.postal_code.strip()
    payment_profile.billing_country_code = data.country_code.strip().upper()
    if not payment_profile.stripe_account_id:
        account = find_connected_account_by_user_id(contractor.user_id)

        if account is None:
            account = create_express_connected_account(
                user_id=contractor.user_id,
                country_code=data.country_code,
            )

        account = update_connected_account_prefill(
            stripe_account_id=account.id,
            user_id=contractor.user_id,
            email=str(contractor.email),
            full_name=contractor.full_name,
            product_description=contractor.about,
            phone=contractor.phone,
            address=data.address.strip(),
            postal_code=data.postal_code.strip(),
            country_code=data.country_code,
            city=contractor.city,
        )

        payment_profile.stripe_account_id = account.id

        try:
            db.commit()
            db.refresh(payment_profile)
        except Exception:
            db.rollback()
            logger.exception(
                "Failed to save Stripe account: user_id=%s",
                current_user.id,
            )
            raise
        
    account_link = create_connected_account_link(
        stripe_account_id=payment_profile.stripe_account_id,
    )

    if not account_link.url:
        raise_payment_error("stripe_account_link_creation_failed")

    return account_link.url

def sync_connected_account_status(db: Session, account: dict) -> None:
    stripe_account_id = account.get("id")
    if not stripe_account_id:
        raise_payment_error("invalid_webhook_payload")

    profile = (
        db.query(PaymentProfile)
        .filter(PaymentProfile.stripe_account_id == stripe_account_id)
        .first()
    )
    if profile is None:
        return

    profile.charges_enabled = bool(account.get("charges_enabled"))
    profile.payouts_enabled = bool(account.get("payouts_enabled"))
    profile.details_submitted = bool(account.get("details_submitted"))
    profile.payout_setup_completed = (
        profile.details_submitted and profile.payouts_enabled
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


# save metode placanja
def create_payment_method_setup_session(
    *,
    db: Session,
    current_user: CurrentUser,
    data: PaymentSetupRequest,
) -> str:
    payment_profile = get_or_create_client_payment_profile(
        db=db,
        user_id=current_user.id,
    )

    address = data.address.strip()
    postal_code = data.postal_code.strip()
    country_code = data.country_code.upper()

    customer_address = {
        "line1": address,
        "postal_code": postal_code,
        "country": country_code,
    }

    payment_profile.billing_address = address
    payment_profile.billing_postal_code = postal_code
    payment_profile.billing_country_code = country_code

    if not payment_profile.stripe_customer_id:
        customer = create_stripe_customer(
            user_id=current_user.id,
            name=current_user.full_name,
            email=current_user.email,
            address=customer_address,
        )

        payment_profile.stripe_customer_id = customer.id
    else:
        update_stripe_customer(
            stripe_customer_id=payment_profile.stripe_customer_id,
            name=current_user.full_name,
            email=current_user.email,
            address=customer_address,
        )

    try:
        db.commit()
        db.refresh(payment_profile)
    except Exception:
        db.rollback()
        raise

    checkout_session = create_payment_setup_session(
        user_id=current_user.id,
        stripe_customer_id=payment_profile.stripe_customer_id,
    )

    if not checkout_session.url:
        raise_payment_error("checkout_session_url_missing")

    return checkout_session.url


def complete_payment_setup(
    *,
    db: Session,
    user_id: int,
    stripe_customer_id: str,
    payment_method: dict | None = None,
    billing_address: dict | None = None,
) -> None:
    profile = get_payment_profile(db, user_id)
    if profile is None or profile.stripe_customer_id != stripe_customer_id:
        raise_payment_error("invalid_webhook_payload")

    profile.payment_setup_completed = True

    if payment_method is not None:
        profile.stripe_payment_method_id = payment_method.get("id")
        card = payment_method.get("card") or {}
        profile.card_brand = (card.get("brand") or "").strip().lower() or None
        profile.card_last4 = str(card.get("last4") or "").strip() or None
        profile.card_exp_month = card.get("exp_month")
        profile.card_exp_year = card.get("exp_year")

    if billing_address is not None:
        profile.billing_address = (billing_address.get("line1") or "").strip() or None
        profile.billing_postal_code = (
            billing_address.get("postal_code") or ""
        ).strip() or None
        profile.billing_country_code = (
            billing_address.get("country") or ""
        ).strip().upper() or None

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


async def create_contract_checkout_session(
    *, db: Session, contract_id: int, current_user_id: int
) -> str:
    contract = await get_contract_payment_details(contract_id)
    if contract.client_id != current_user_id:
        raise_payment_error("only_clients_can_pay")
    if contract.status != "completed":
        raise_payment_error("contract_not_payable")

    payment = db.query(JobPayment).filter(JobPayment.contract_id == contract_id).first()
    if payment is None:
        payment = JobPayment(
            contract_id=contract.contract_id,
            application_id=contract.application_id,
            job_id=contract.job_id,
            client_id=contract.client_id,
            contractor_id=contract.contractor_id,
            job_title=contract.job_title,
            amount_minor=contract.amount_minor,
            currency=contract.currency.lower(),
            status="pending",
        )
        db.add(payment)
        db.flush()

    if payment.status == "paid":
        raise_payment_error("payment_already_paid")

    client_profile = get_or_create_client_payment_profile(
        db,
        current_user_id,
    )

    if not client_profile.stripe_customer_id:
        customer = create_stripe_customer(
            user_id=current_user_id,
            name=contract.client_name,
            email=str(contract.client_email),
        )
        client_profile.stripe_customer_id = customer.id

    contractor_profile = get_payment_profile(
        db,
        contract.contractor_id,
    )

    if (
        contractor_profile is None
        or contractor_profile.role != "contractor"
        or not contractor_profile.stripe_account_id
        or not contractor_profile.details_submitted
        or not contractor_profile.payouts_enabled
    ):
        raise_payment_error("contractor_payout_not_ready")

    checkout = create_checkout_session(
        payment=payment,
        stripe_customer_id=client_profile.stripe_customer_id,
        contractor_stripe_account_id=contractor_profile.stripe_account_id,
    )

    if not checkout.url:
        raise_payment_error("checkout_session_url_missing")

    payment.stripe_checkout_session_id = checkout.id
    payment.checkout_attempt += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return checkout.url


def expire_pending_job_payments(db: Session, pending_timeout: timedelta) -> int:
    cutoff = datetime.now(timezone.utc) - pending_timeout
    payments = list(
        db.scalars(
            select(JobPayment)
            .where(
                JobPayment.status == "pending",
                JobPayment.created_at <= cutoff,
            )
            .with_for_update(skip_locked=True)
        ).all()
    )
    if not payments:
        return 0
    for payment in payments:
        payment.status = "overdue"
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return len(payments)
