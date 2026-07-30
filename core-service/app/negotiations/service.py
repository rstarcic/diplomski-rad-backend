from app.applications.models import Application
from app.applications.service import (
    authorize_application_participant,
    expire_stale_negotiation,
    get_application_with_job,
)
from app.integrations.client import create_contract
from app.integrations.schemas import (ContractCreateRequest, ContractJob,
                                      ContractParty, ContractTermsRequest)
from app.jobs.models import Job
from app.negotiations.models import Negotiation, NegotiationEdit
from app.negotiations.schemas import (
    CounterOfferRequest,
    CounterOfferResponse,
    NegotiationEditResponse,
)
from app.negotiations.terms import extract_job_terms, extract_negotiation_terms
from app.profiles.models import Profile
from app.profiles.services.profile_repository import (
    get_client_profile_by_user_id, get_contractor_profile_by_user_id,
    get_profile_by_user_id)
from errors import raise_core_error
from sqlalchemy import select
from sqlalchemy.orm import Session


MAX_NEGOTIATION_ROUNDS = 3


def _get_latest_negotiation_edit(
    db: Session,
    negotiation_id: int,
) -> NegotiationEdit | None:
    return db.scalar(
        select(NegotiationEdit)
        .where(NegotiationEdit.negotiation_id == negotiation_id)
        .order_by(NegotiationEdit.round_number.desc())
        .limit(1)
    )


def _resolve_contract_terms_for_acceptance(
    db: Session,
    application: Application,
    job: Job,
    user: Profile,
    *,
    for_update: bool = False,
) -> tuple[Job | NegotiationEdit, Negotiation | None]:
    negotiation = select(Negotiation).where(
        Negotiation.application_id == application.id
    )

    if for_update:
        negotiation = negotiation.with_for_update()

    negotiation = db.scalar(negotiation)

    # nema pregovora: vrijede originalni uvjeti iz Joba.
    if negotiation is None:
        if user.role != "contractor":
            raise_core_error("contractor_response_required")

        terms = extract_job_terms(job)

        return terms, None

    negotiation_updates = list(
        db.scalars(
            select(NegotiationEdit)
            .where(NegotiationEdit.negotiation_id == negotiation.id)
            .order_by(NegotiationEdit.round_number.asc())
        ).all()
    )

    if expire_stale_negotiation(db, negotiation, negotiation_updates):
        raise_core_error("negotiation_already_finished")

    # postoji pregovor: prihvaća se zadnja ponuda.
    if negotiation.status == "pending_client":
        expected_role = "client"

    elif negotiation.status == "pending_contractor":
        expected_role = "contractor"

    else:
        raise_core_error("negotiation_already_finished")

    if user.role != expected_role:
        raise_core_error("not_your_turn")

    latest_offer = _get_latest_negotiation_edit(
        db=db,
        negotiation_id=negotiation.id,
    )

    if latest_offer is None:
        raise_core_error("negotiation_offer_not_found")

    terms = extract_negotiation_terms(latest_offer)

    return terms, negotiation


async def accept_application_terms(
    db: Session,
    job_id: int,
    application_id: int,
    user_id: int,
):
    user = get_profile_by_user_id(db, user_id)

    if user is None:
        raise_core_error("user_not_found")

    # dohvat applicationa i joba
    result = get_application_with_job(
        db=db,
        job_id=job_id,
        application_id=application_id,
        for_update=True,
    )

    if result is None:
        raise_core_error("application_not_found")

    application, job = result

    # autorizacija trenutnog korisnika
    authorize_application_participant(
        user=user,
        application=application,
        job=job,
    )

    if application.status != "selected":
        raise_core_error("application_not_selected")

    # dohvat obje ugovorne strane
    client = get_client_profile_by_user_id(db, job.client_id)
    contractor = get_contractor_profile_by_user_id(
        db,
        application.contractor_id,
    )

    if client is None:
        raise_core_error("client_not_found")

    if contractor is None:
        raise_core_error("contractor_not_found")

    # terms dolaze iz Joba ili zadnje ponude pregovora.
    terms, negotiation = _resolve_contract_terms_for_acceptance(
        db=db,
        application=application,
        job=job,
        user=user,
        for_update=True,
    )

    # snapshot Contracta
    contract_request = ContractCreateRequest(
        application_id=application.id,
        negotiation_id=negotiation.id if negotiation else None,
        client=ContractParty(
            user_id=client.user_id,
            full_name=client.full_name,
            email=client.email,
            phone=client.phone,
            country=client.country,
            city=client.city,
        ),
        contractor=ContractParty(
            user_id=contractor.user_id,
            full_name=contractor.full_name,
            email=contractor.email,
            phone=contractor.phone,
            country=contractor.country,
            city=contractor.city,
        ),
        job=ContractJob(
            id=job.id,
            title=job.title,
            description=job.description,
        ),
        terms=ContractTermsRequest(
            budget_amount=terms.budget_amount,
            budget_type=terms.budget_type,
            currency=job.currency,
            duration=terms.duration,
            hours_per_week=terms.hours_per_week,
            deliverables=terms.deliverables,
        ),
    )

    # slanje contract servisu
    contract = await create_contract(contract_request)

    application.status = "accepted"
    job.status = "awaiting_contract"

    if negotiation is not None:
        negotiation.status = "accepted"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return contract


def reject_application_terms(
    db: Session,
    job_id: int,
    application_id: int,
    current_user: Profile,
) -> Application:
    result = get_application_with_job(
        db=db,
        job_id=job_id,
        application_id=application_id,
        for_update=True,
    )

    if result is None:
        raise_core_error("application_not_found")

    application, job = result

    authorize_application_participant(
        user=current_user,
        application=application,
        job=job,
    )

    if application.status != "selected":
        raise_core_error("application_not_selected")

    negotiation = db.scalar(
        select(Negotiation)
        .where(Negotiation.application_id == application.id)
        .with_for_update()
    )

    if negotiation is not None:
        negotiation_updates = list(
            db.scalars(
                select(NegotiationEdit)
                .where(NegotiationEdit.negotiation_id == negotiation.id)
                .order_by(NegotiationEdit.round_number.asc())
            ).all()
        )

        if expire_stale_negotiation(db, negotiation, negotiation_updates):
            raise_core_error("negotiation_already_finished")

        negotiation.status = "rejected"

    if current_user.role == "client":
        application.status = "rejected"
    elif current_user.role == "contractor":
        application.status = "withdrawn"
    else:
        raise_core_error("forbidden")

    job.status = "cancelled"

    try:
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise

    return application


def submit_application_counter_offer(
    db: Session,
    job_id: int,
    application_id: int,
    current_user: Profile,
    data: CounterOfferRequest,
) -> CounterOfferResponse:
    result = get_application_with_job(
        db=db,
        job_id=job_id,
        application_id=application_id,
        for_update=True,
    )

    if result is None:
        raise_core_error("application_not_found")

    application, job = result

    authorize_application_participant(
        user=current_user,
        application=application,
        job=job,
    )

    if application.status != "selected":
        raise_core_error("application_not_selected")

    negotiation = db.scalar(
        select(Negotiation)
        .where(Negotiation.application_id == application.id)
        .with_for_update()
    )

    latest_offer = None

    if negotiation is None:
        if current_user.role != "contractor":
            raise_core_error("contractor_response_required")

        negotiation = Negotiation(
            job_id=job.id,
            application_id=application.id,
            client_id=job.client_id,
            contractor_id=application.contractor_id,
            status="pending_client",
        )
        db.add(negotiation)
        db.flush()
        next_round_number = 1
    else:
        negotiation_updates = list(
            db.scalars(
                select(NegotiationEdit)
                .where(NegotiationEdit.negotiation_id == negotiation.id)
                .order_by(NegotiationEdit.round_number.asc())
            ).all()
        )

        if expire_stale_negotiation(db, negotiation, negotiation_updates):
            raise_core_error("negotiation_already_finished")

        if negotiation.status not in {"pending_client", "pending_contractor"}:
            raise_core_error("negotiation_already_finished")

        expected_role = (
            "client"
            if negotiation.status == "pending_client"
            else "contractor"
        )

        if current_user.role != expected_role:
            raise_core_error("not_your_turn")

        latest_offer = _get_latest_negotiation_edit(
            db=db,
            negotiation_id=negotiation.id,
        )

        if (
            latest_offer is not None
            and latest_offer.round_number >= MAX_NEGOTIATION_ROUNDS
        ):
            negotiation.status = "rejected"
            application.status = "rejected"
            job.status = "cancelled"

            try:
                db.commit()
            except Exception:
                db.rollback()
                raise

            raise_core_error("negotiation_round_limit_reached")

        next_round_number = (
            latest_offer.round_number + 1
            if latest_offer is not None
            else 1
        )
        negotiation.status = (
            "pending_contractor"
            if current_user.role == "client"
            else "pending_client"
        )

    update = NegotiationEdit(
        negotiation_id=negotiation.id,
        round_number=next_round_number,
        submitted_by=current_user.role,
        budget_amount=data.budget_amount,
        budget_type=data.budget_type,
        duration=data.duration,
        hours_per_week=data.hours_per_week,
        deliverables=data.deliverables,
        message=data.message,
    )
    db.add(update)

    try:
        db.commit()
        db.refresh(negotiation)
        db.refresh(update)
    except Exception:
        db.rollback()
        raise

    return CounterOfferResponse(
        negotiation_id=negotiation.id,
        negotiation_status=negotiation.status,
        update=NegotiationEditResponse.model_validate(update),
    )
