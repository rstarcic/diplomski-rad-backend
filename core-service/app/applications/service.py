from datetime import datetime, timedelta, timezone

from app.applications.models import Application
from app.applications.schemas import (
    ApplicationContractorPreview,
    ApplicationJobSummary,
    ApplicationSummary,
    ApplicationSummaryDetail,
    JobApplicationDetailResponse,
    JobApplicationItemResponse,
)
from app.jobs.models import Job
from app.negotiations.models import Negotiation, NegotiationEdit
from app.negotiations.schemas import NegotiationEditResponse, NegotiationSummaryResponse
from app.profiles.models import Profile
from app.profiles.schemas import ContractorPublicProfile
from app.reviews.service import get_reviews_for_target
from sqlalchemy import select
from sqlalchemy.orm import Session

NEGOTIATION_RESPONSE_TIMEOUT = timedelta(days=1)
PENDING_NEGOTIATION_STATUSES = {"pending_client", "pending_contractor"}


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def expire_stale_negotiation(
    db: Session,
    negotiation: Negotiation,
    negotiation_updates: list[NegotiationEdit],
) -> None:
    if negotiation.status not in PENDING_NEGOTIATION_STATUSES:
        return

    last_activity_at = (
        negotiation_updates[-1].submitted_at
        if negotiation_updates
        else negotiation.created_at
    )

    elapsed = datetime.now(timezone.utc) - _as_aware_utc(last_activity_at)
    if elapsed < NEGOTIATION_RESPONSE_TIMEOUT:
        return

    negotiation.status = "expired"
    negotiation.updated_at = datetime.now(timezone.utc)
    db.commit()


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


def get_job_application_detail(
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
        negotiationUpdates=[
            NegotiationEditResponse.model_validate(update)
            for update in negotiation_updates
        ],
        contract=None,
        payment=None,
    )
