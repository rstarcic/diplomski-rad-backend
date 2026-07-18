from app.applications.models import Application
from app.jobs.models import Job
from app.negotiations.models import Negotiation, NegotiationEdit
from app.profiles.models import Profile
from app.profiles.schemas import ClientPublicStat, ContractorPublicStat
from app.reviews.schemas import TargetReviewsResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def count_completed_jobs_for_contractor(db: Session, contractor_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(
                Application.contractor_id == contractor_id,
                Application.status == "accepted",
                Job.status == "completed_by_client",
            )
        )
        or 0
    )


def count_active_contracts_for_contractor(db: Session, contractor_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(
                Application.contractor_id == contractor_id,
                Application.status == "accepted",
                Job.status.in_(("in_progress", "done_by_contractor")),
            )
        )
        or 0
    )


def count_jobs_posted_by_client(db: Session, client_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(Job).where(Job.client_id == client_id)
        )
        or 0
    )


def count_completed_jobs_for_client(db: Session, client_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Job)
            .where(
                Job.client_id == client_id,
                Job.status == "completed_by_client",
            )
        )
        or 0
    )


def count_active_jobs_for_client(db: Session, client_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Job)
            .where(
                Job.client_id == client_id,
                Job.status == "in_progress",
            )
        )
        or 0
    )


def get_average_response_time_for_contractor(
    db: Session,
    contractor_id: int,
) -> str:
    average_seconds = db.scalar(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    NegotiationEdit.submitted_at - Negotiation.created_at,
                )
            )
        )
        .select_from(Negotiation)
        .join(Application, Application.id == Negotiation.application_id)
        .join(
            NegotiationEdit,
            NegotiationEdit.negotiation_id == Negotiation.id,
        )
        .where(
            Application.contractor_id == contractor_id,
            NegotiationEdit.submitted_by == "contractor",
        )
    )

    if average_seconds is None:
        return "N/A"

    minutes = round(average_seconds / 60)

    if minutes < 1:
        return "<1m"

    if minutes < 60:
        return f"{minutes}m"

    hours = round(minutes / 60)

    if hours < 24:
        return f"{hours}h"

    days = round(hours / 24)
    return f"{days}d"


def get_average_response_time_for_client(
    db: Session,
    client_id: int,
) -> str:
    average_seconds = db.scalar(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    NegotiationEdit.submitted_at - Negotiation.created_at,
                )
            )
        )
        .select_from(Negotiation)
        .join(
            NegotiationEdit,
            NegotiationEdit.negotiation_id == Negotiation.id,
        )
        .where(
            Negotiation.client_id == client_id,
            NegotiationEdit.submitted_by == "client",
        )
    )

    if average_seconds is None:
        return "N/A"

    minutes = round(average_seconds / 60)

    if minutes < 1:
        return "<1m"

    if minutes < 60:
        return f"{minutes}m"

    hours = round(minutes / 60)

    if hours < 24:
        return f"{hours}h"

    days = round(hours / 24)
    return f"{days}d"


def calculate_profile_strength(
    contractor: Profile,
    skills_count: int,
    portfolio_count: int,
) -> str:
    completed_fields = 0
    total_fields = 7

    if contractor.full_name:
        completed_fields += 1
    if contractor.profile_picture or contractor.profile_picture_blob:
        completed_fields += 1
    if contractor.about:
        completed_fields += 1
    if contractor.city and contractor.country:
        completed_fields += 1
    if contractor.phone:
        completed_fields += 1
    if skills_count > 0:
        completed_fields += 1
    if portfolio_count > 0:
        completed_fields += 1

    percentage = round((completed_fields / total_fields) * 100)
    return f"{percentage}%"


def build_contractor_public_stats(
    contractor: Profile,
    completed_jobs: int,
    active_contracts: int,
    average_response_time: str,
    skills_count: int,
    portfolio_count: int,
) -> list[ContractorPublicStat]:
    return [
        ContractorPublicStat(
            id="completedJobs",
            value=completed_jobs,
            subtitle="Jobs completed",
        ),
        ContractorPublicStat(
            id="activeContracts",
            value=active_contracts,
            subtitle="Active contracts",
        ),
        ContractorPublicStat(
            id="averageResponseTime",
            value=average_response_time,
            subtitle="Avg. negotiation reply",
        ),
        ContractorPublicStat(
            id="profileStrength",
            value=calculate_profile_strength(
                contractor=contractor,
                skills_count=skills_count,
                portfolio_count=portfolio_count,
            ),
            subtitle="Profile completed",
        ),
    ]


def build_client_public_stats(
    jobs_posted: int,
    jobs_completed: int,
    active_jobs: int,
    average_response_time: str,
) -> list[ClientPublicStat]:
    return [
        ClientPublicStat(
            id="jobsPosted",
            value=jobs_posted,
            subtitle="Jobs posted",
        ),
        ClientPublicStat(
            id="jobsCompleted",
            value=jobs_completed,
            subtitle="Jobs completed",
        ),
        ClientPublicStat(
            id="activeJobs",
            value=active_jobs,
            subtitle="Active jobs",
        ),
        ClientPublicStat(
            id="averageResponseTime",
            value=average_response_time,
            subtitle="Avg. negotiation reply",
        ),
    ]
