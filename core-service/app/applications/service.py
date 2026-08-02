from datetime import UTC, datetime, timedelta

from app.applications.models import Application
from app.applications.schemas import (
    ApplicationContractorPreview,
    ApplicationCreate,
    ApplicationCreateResponse,
    ApplicationDecisionResponse,
    ApplicationJobSummary,
    ApplicationSummary,
    ApplicationSummaryDetail,
    JobApplicationDetailResponse,
    JobApplicationItemResponse,
    MyApplicationClientSummary,
    MyApplicationDetailResponse,
    MyApplicationItemResponse,
    MyApplicationJobSummary,
    MyApplicationSummary,
)
from app.integrations.client import (
    get_contract_summary,
    get_payment_summary,
    update_contract_status_for_job,
)
from app.integrations.schemas import ContractPartySummary, ContractPlatformSummary
from app.jobs.models import Job
from app.jobs.schemas import JobResponse
from app.negotiations.models import Negotiation, NegotiationEdit
from app.negotiations.schemas import NegotiationEditResponse, NegotiationSummaryResponse
from app.profiles.models import Profile
from app.profiles.schemas import ClientPublicProfile, ContractorPublicProfile
from app.reviews.service import get_reviews_for_target
from errors import raise_core_error
from sqlalchemy import select, update
from sqlalchemy.orm import Session

NEGOTIATION_RESPONSE_TIMEOUT = timedelta(days=1)
PENDING_NEGOTIATION_STATUSES = {"pending_client", "pending_contractor"}


def authorize_application_participant(
    user: Profile,
    application: Application,
    job: Job,
) -> None:
    if user.role == "client":
        if job.client_id != user.user_id:
            raise_core_error("forbidden")

    elif user.role == "contractor":
        if application.contractor_id != user.user_id:
            raise_core_error("forbidden")

    else:
        raise_core_error("forbidden")


def create_job_application(
    db: Session,
    job_id: int,
    contractor_id: int,
    data: ApplicationCreate,
) -> ApplicationCreateResponse:
    job = db.scalar(select(Job).where(Job.id == job_id))

    if job is None:
        raise_core_error("job_not_found")

    if job.deadline <= datetime.now(UTC):
        raise_core_error("application_deadline_expired")

    if job.status != "open":
        raise_core_error("job_not_open_for_applications")

    existing_application = db.scalar(
        select(Application.id).where(
            Application.job_id == job_id,
            Application.contractor_id == contractor_id,
        )
    )

    if existing_application is not None:
        raise_core_error("application_already_exists")

    application = Application(
        job_id=job_id,
        contractor_id=contractor_id,
        cover_letter=data.cover_letter.strip(),
        status="pending",
    )
    db.add(application)
    try:
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise
    return ApplicationCreateResponse.model_validate(application)


CLIENT_ALLOWED_DECISIONS = {"selected", "rejected"}


async def withdraw_job_application(
    db: Session,
    application_id: int,
    contractor_id: int,
) -> ApplicationDecisionResponse:
    row = db.execute(
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(
            Application.id == application_id,
            Application.contractor_id == contractor_id,
        )
        .with_for_update()
    ).one_or_none()

    if row is None:
        raise_core_error("application_not_found")

    application, job = row

    if application.status == "withdrawn":
        return ApplicationDecisionResponse(id=application.id, status=application.status)

    if application.status not in {"pending", "selected", "accepted"}:
        raise_core_error("application_cannot_be_withdrawn")

    if application.status == "accepted":
        if job.status not in {"awaiting_contract", "in_progress"}:
            raise_core_error("application_cannot_be_withdrawn")
        await update_contract_status_for_job(job.id, "cancel")

    negotiation = db.scalar(
        select(Negotiation)
        .where(Negotiation.application_id == application.id)
        .with_for_update()
    )
    if negotiation is not None and negotiation.status in PENDING_NEGOTIATION_STATUSES:
        negotiation.status = "rejected"

    previous_status = application.status
    application.status = "withdrawn"

    # A pending application is only one candidate, so its withdrawal must not
    # close the client's job. Selected/accepted applications own the job flow.
    if previous_status in {"selected", "accepted"}:
        job.status = "cancelled"

    try:
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise

    return ApplicationDecisionResponse(id=application.id, status=application.status)


def decide_job_application(
    db: Session,
    client_id: int,
    job_id: int,
    application_id: int,
    decision: str,
) -> ApplicationDecisionResponse:
    decision = decision.lower().strip()

    if decision not in CLIENT_ALLOWED_DECISIONS:
        raise_core_error("invalid_application_decision")

    row = db.execute(
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.id == job_id,
            Job.client_id == client_id,
            Application.id == application_id,
            Application.job_id == job_id,
        )
        .with_for_update()
    ).one_or_none()

    if row is None:
        raise_core_error("application_not_found")

    application, job = row

    if application.status == decision:
        return ApplicationDecisionResponse(
            id=application.id,
            status=application.status,
        )

    if application.status != "pending":
        raise_core_error("application_decision_cannot_be_changed")

    if decision == "selected" and job.status != "open":
        raise_core_error("job_not_open_for_applications")

    try:
        if decision == "rejected":
            application.status = "rejected"

        elif decision == "selected":
            application.status = "selected"
            job.status = "awaiting_contract"

            db.execute(
                update(Application)
                .where(
                    Application.job_id == job_id,
                    Application.id != application.id,
                    Application.status == "pending",
                )
                .values(status="rejected")
            )

        db.commit()
        db.refresh(application)

    except Exception:
        db.rollback()
        raise

    return ApplicationDecisionResponse(
        id=application.id,
        status=application.status,
    )


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def expire_stale_negotiation(
    db: Session,
    negotiation: Negotiation,
    negotiation_updates: list[NegotiationEdit],
) -> bool:
    if negotiation.status not in PENDING_NEGOTIATION_STATUSES:
        return False

    last_activity_at = (
        negotiation_updates[-1].submitted_at
        if negotiation_updates
        else negotiation.created_at
    )

    elapsed = datetime.now(UTC) - _as_aware_utc(last_activity_at)
    if elapsed < NEGOTIATION_RESPONSE_TIMEOUT:
        return False

    application = db.scalar(
        select(Application).where(
            Application.id == negotiation.application_id,
        )
    )
    job = db.scalar(select(Job).where(Job.id == negotiation.job_id))

    waiting_for_role = negotiation.status
    negotiation.status = "expired"
    negotiation.updated_at = datetime.now(UTC)

    if application is not None and application.status == "selected":
        application.status = (
            "rejected" if waiting_for_role == "pending_client" else "withdrawn"
        )

    if job is not None:
        job.status = "cancelled"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return True


def get_my_applications(
    db: Session,
    contractor_id: int,
) -> list[MyApplicationItemResponse]:
    rows = db.execute(
        select(Application, Job, Profile)
        .join(Job, Job.id == Application.job_id)
        .join(Profile, Profile.user_id == Job.client_id)
        .where(Application.contractor_id == contractor_id)
        .order_by(Application.created_at.desc())
    ).all()

    return [
        MyApplicationItemResponse(
            job=MyApplicationJobSummary(
                id=job.id,
                title=job.title,
                category=job.category,
            ),
            client=MyApplicationClientSummary(
                user_id=client.user_id,
                full_name=client.full_name,
                city=client.city,
                country=client.country,
                profile_picture=client.display_profile_picture,
            ),
            application=MyApplicationSummary(
                id=application.id,
                status=application.status,
                cover_letter=application.cover_letter,
                created_at=application.created_at,
            ),
        )
        for application, job, client in rows
    ]


async def get_my_application_detail(
    db: Session,
    contractor_id: int,
    application_id: int,
) -> MyApplicationDetailResponse | None:
    row = db.execute(
        select(Application, Job, Profile)
        .join(Job, Job.id == Application.job_id)
        .join(Profile, Profile.user_id == Job.client_id)
        .where(
            Application.id == application_id,
            Application.contractor_id == contractor_id,
        )
    ).one_or_none()

    if row is None:
        return None

    application, job, client = row

    reviews = get_reviews_for_target(
        db=db,
        target_type="client",
        target_id=client.user_id,
    )

    negotiation = db.scalar(
        select(Negotiation).where(
            Negotiation.application_id == application.id,
        )
    )

    negotiation_updates = []
    if negotiation is not None:
        negotiation_updates = db.scalars(
            select(NegotiationEdit)
            .where(NegotiationEdit.negotiation_id == negotiation.id)
            .order_by(NegotiationEdit.round_number.asc())
        ).all()

        expire_stale_negotiation(
            db=db,
            negotiation=negotiation,
            negotiation_updates=negotiation_updates,
        )

    contract = await get_contract_summary(application_id)

    if contract is not None:
        if not contract.platform_name:
            contract.platform_name = "WorkLink"
        if not contract.client_name:
            contract.client_name = client.full_name
        if not contract.client:
            contract.client = ContractPartySummary(
                user_id=client.user_id,
                full_name=client.full_name,
                email=client.email,
            )

        contractor_profile = db.scalar(
            select(Profile).where(Profile.user_id == application.contractor_id)
        )
        if contractor_profile is not None:
            if not contract.contractor_name:
                contract.contractor_name = contractor_profile.full_name
            if not contract.contractor:
                contract.contractor = ContractPartySummary(
                    user_id=contractor_profile.user_id,
                    full_name=contractor_profile.full_name,
                    email=contractor_profile.email,
                )

        if not contract.platform:
            contract.platform = ContractPlatformSummary(
                name=contract.platform_name or "WorkLink"
            )

    payment = (
        await get_payment_summary(application_id) if contract is not None else None
    )

    return MyApplicationDetailResponse(
        application=MyApplicationSummary(
            id=application.id,
            status=application.status,
            cover_letter=application.cover_letter,
            created_at=application.created_at,
        ),
        job=JobResponse.model_validate(job),
        client=ClientPublicProfile(
            user_id=client.user_id,
            full_name=client.full_name,
            profile_picture=client.display_profile_picture,
            email=client.email,
            phone=client.phone,
            city=client.city,
            country=client.country,
            created_at=client.created_at,
            about=client.about,
        ),
        reviews=reviews,
        negotiation=(
            NegotiationSummaryResponse.model_validate(negotiation)
            if negotiation is not None
            else None
        ),
        negotiation_updates=[
            NegotiationEditResponse.model_validate(update)
            for update in negotiation_updates
        ],
        contract=contract,
        payment=payment,
    )


async def get_job_application_detail(
    db: Session,
    client_id: int,
    job_id: int,
    application_id: int,
) -> JobApplicationDetailResponse | None:
    row = db.execute(
        select(Application, Profile)
        .join(Profile, Profile.user_id == Application.contractor_id)
        .join(Job, Job.id == Application.job_id)
        .where(
            Job.id == job_id,
            Job.client_id == client_id,
            Application.id == application_id,
            Application.job_id == job_id,
        )
    ).one_or_none()

    if row is None:
        return None

    application, contractor = row

    negotiation = db.scalar(
        select(Negotiation).where(
            Negotiation.application_id == application.id,
        )
    )

    negotiation_updates = []
    if negotiation is not None:
        negotiation_updates = db.scalars(
            select(NegotiationEdit)
            .where(NegotiationEdit.negotiation_id == negotiation.id)
            .order_by(NegotiationEdit.round_number.asc())
        ).all()
        expire_stale_negotiation(db, negotiation, negotiation_updates)

    reviews = get_reviews_for_target(
        db=db,
        target_type="contractor",
        target_id=contractor.user_id,
    )

    contract = await get_contract_summary(application_id)
    payment = (
        await get_payment_summary(application_id) if contract is not None else None
    )

    return JobApplicationDetailResponse(
        application=ApplicationSummaryDetail(
            id=application.id,
            status=application.status,
            cover_letter=application.cover_letter,
            created_at=application.created_at,
        ),
        contractor=ContractorPublicProfile(
            user_id=contractor.user_id,
            full_name=contractor.full_name,
            profile_picture=contractor.display_profile_picture,
            email=contractor.email,
            phone=contractor.phone,
            city=contractor.city,
            country=contractor.country,
            created_at=contractor.created_at,
            about=contractor.about,
        ),
        reviews=reviews,
        negotiation=(
            NegotiationSummaryResponse.model_validate(negotiation)
            if negotiation is not None
            else None
        ),
        negotiation_updates=[
            NegotiationEditResponse.model_validate(update)
            for update in negotiation_updates
        ],
        contract=contract,
        payment=payment,
    )


def get_job_applications(
    db: Session, client_id: int, job_id: int
) -> list[JobApplicationItemResponse] | None:
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.client_id == client_id,
        )
    )

    if job is None:
        return None

    rows = db.execute(
        select(Application, Profile)
        .join(Profile, Profile.user_id == Application.contractor_id)
        .where(Application.job_id == job_id)
        .order_by(Application.created_at.desc())
    ).all()

    return [
        JobApplicationItemResponse(
            contractor=ApplicationContractorPreview(
                user_id=contractor.user_id,
                full_name=contractor.full_name,
                profile_picture=contractor.display_profile_picture,
                city=contractor.city,
                country=contractor.country,
            ),
            application=ApplicationSummary(
                id=application.id,
                status=application.status,
                cover_letter=application.cover_letter,
            ),
            job=ApplicationJobSummary(
                id=job.id,
                title=job.title,
            ),
        )
        for application, contractor in rows
    ]


def get_application_with_job(
    db: Session,
    job_id: int,
    application_id: int,
    *,
    for_update: bool = False,
) -> tuple[Application, Job] | None:
    query = (
        select(Application, Job)
        .join(Job, Job.id == Application.job_id)
        .where(
            Application.id == application_id,
            Application.job_id == job_id,
            Job.id == job_id,
        )
    )

    if for_update:
        query = query.with_for_update()

    row = db.execute(query).one_or_none()

    if row is None:
        return None

    application, job = row
    return application, job
