from datetime import datetime, timezone

from app.jobs.models import Job
from app.jobs.schemas import (
    JobCreate,
    JobResponse,
    JobSearchClient,
    JobSearchItem,
    JobSearchItemResponse,
    JobSummaryResponse,
    JobUpdate,
)
from app.profiles.models import Profile
from errors import raise_core_error
from sqlalchemy.orm import Session


def build_job_search_item(
    job: Job,
    client: Profile,
) -> JobSearchItemResponse:
    return JobSearchItemResponse(
        job=JobSearchItem(
            id=job.id,
            title=job.title,
            category=job.category,
            description=job.description,
            location_type=job.location_type,
            location=job.location,
            budget_type=job.budget_type,
            budget_amount=job.budget_amount,
            currency=job.currency,
            status=job.status,
            created_at=job.created_at,
            deadline=job.deadline,
        ),
        client=JobSearchClient(
            user_id=client.user_id,
            full_name=client.full_name,
            profile_picture=client.display_profile_picture,
        ),
    )


def create_job(db: Session, client_id: int, data: JobCreate) -> JobResponse:
    new_job = Job(
        client_id=client_id,
        currency="EUR",
        status="open",
        **data.model_dump(),
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return JobResponse.model_validate(new_job)


def get_open_jobs(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    location_type: str | None = None,
    location: str | None = None,
    budget_type: str | None = None,
    min_budget: float | None = None,
    max_budget: float | None = None,
) -> list[JobSearchItemResponse]:
    query = (
        db.query(Job, Profile)
        .join(Profile, Profile.user_id == Job.client_id)
        .filter(Job.status == "open", Job.deadline > datetime.now(timezone.utc))
        .order_by(Job.created_at.desc())
    )

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(pattern),
                Job.category.ilike(pattern),
                Job.description.ilike(pattern),
            )
        )

    if category:
        query = query.filter(Job.category == category)

    if location_type:
        query = query.filter(Job.location_type == location_type)

    if location:
        query = query.filter(Job.location == location)

    if budget_type:
        query = query.filter(Job.budget_type == budget_type)

    if min_budget is not None:
        query = query.filter(Job.budget_amount >= min_budget)

    if max_budget is not None:
        query = query.filter(Job.budget_amount <= max_budget)

    rows = query.order_by(Job.created_at.desc()).all()

    return [build_job_search_item(job, client) for job, client in rows]


def get_job_by_id(db: Session, client_id: int, job_id: int) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id, Job.client_id == client_id).first()
    if not job:
        return None

    return JobResponse.model_validate(job)


def update_job(
    db: Session,
    client_id: int,
    job_id: int,
    data: JobUpdate,
) -> JobResponse | None:
    job = db.query(Job).filter(Job.id == job_id, Job.client_id == client_id).first()

    if not job:
        return None

    if job.status != "open":
        raise_core_error("job_cannot_be_updated")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return JobResponse.model_validate(job)


def get_my_jobs(db: Session, client_id: int) -> list[JobSummaryResponse]:
    jobs = (
        db.query(Job)
        .filter(Job.client_id == client_id)
        .order_by(Job.updated_at.desc())
        .all()
    )

    return [
        JobSummaryResponse(
            id=job.id,
            title=job.title,
            category=job.category,
            location_type=job.location_type,
            location=job.location,
            budget_type=job.budget_type,
            status=job.status,
            deadline=job.deadline,
            updated_at=job.updated_at,
        )
        for job in jobs
    ]
