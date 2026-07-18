from datetime import datetime, timezone

from app.applications.models import Application
from app.integrations.client import (
    create_pending_payment,
    update_contract_status_for_job,
)
from app.jobs.models import Job
from app.jobs.schemas import (
    JobCreate,
    JobDetailsPageResponse,
    JobFilterOptionsResponse,
    JobResponse,
    JobSearchClient,
    JobSearchItem,
    JobSearchItemResponse,
    JobSummaryResponse,
    JobUpdate,
)
from app.pagination import PaginatedResponse
from app.profiles.models import Profile
from app.profiles.schemas import ClientPublicProfile
from app.reviews.service import get_reviews_for_target
from errors import raise_core_error
from sqlalchemy import or_, select
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
    source_job_id = data.source_job_id

    if source_job_id is not None:
        source_job = db.scalar(
            select(Job).where(Job.id == source_job_id).with_for_update()
        )

        if source_job is None:
            raise_core_error("source_job_not_found")

        if source_job.client_id != client_id:
            raise_core_error("source_job_forbidden")

        if source_job.status != "cancelled":
            raise_core_error("source_job_not_cancelled")

        replacement_exists = db.scalar(
            select(Job.id).where(Job.source_job_id == source_job_id)
        )

        if replacement_exists is not None:
            raise_core_error("replacement_job_already_exists")

    new_job = Job(
        client_id=client_id,
        source_job_id=source_job_id,
        currency="EUR",
        status="open",
        **data.model_dump(exclude={"source_job_id"}),
    )

    try:
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
    except Exception:
        db.rollback()
        raise

    return JobResponse.model_validate(new_job)


def get_job_filter_options(db: Session) -> JobFilterOptionsResponse:
    active_jobs = (
        Job.status == "open",
        Job.deadline > datetime.now(timezone.utc),
    )

    categories = [
        value
        for (value,) in (
            db.query(Job.category)
            .filter(*active_jobs, Job.category.isnot(None), Job.category != "")
            .distinct()
            .order_by(Job.category)
            .all()
        )
    ]

    cities = [
        value
        for (value,) in (
            db.query(Job.location)
            .filter(
                *active_jobs,
                Job.location_type.in_(["on_site", "hybrid"]),
                Job.location.isnot(None),
                Job.location != "",
            )
            .distinct()
            .order_by(Job.location)
            .all()
        )
    ]

    return JobFilterOptionsResponse(
        categories=categories,
        cities=cities,
    )


def get_job_details(
    db: Session,
    job_id: int,
    contractor_id: int,
) -> JobDetailsPageResponse | None:
    row = (
        db.query(Job, Profile)
        .join(Profile, Profile.user_id == Job.client_id)
        .filter(
            Job.id == job_id,
            Job.status == "open",
            Job.deadline > datetime.now(timezone.utc),
        )
        .one_or_none()
    )

    if row is None:
        return None

    job, client = row
    application_status = (
        db.query(Application.status)
        .filter(
            Application.job_id == job.id,
            Application.contractor_id == contractor_id,
        )
        .scalar()
    )
    reviews = get_reviews_for_target(
        db=db,
        target_type="client",
        target_id=client.user_id,
    )

    return JobDetailsPageResponse(
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
        already_applied=application_status is not None,
        application_status=application_status,
    )


def get_open_jobs(
    db: Session,
    search: str | None = None,
    category: str | None = None,
    location: str | None = None,
    location_type: str | None = None,
    budget_type: str | None = None,
    min_budget: float | None = None,
    max_budget: float | None = None,
    page: int = 1,
    page_size: int = 16,
) -> PaginatedResponse[JobSearchItemResponse]:
    query = (
        db.query(Job, Profile)
        .join(Profile, Profile.user_id == Job.client_id)
        .filter(Job.status == "open", Job.deadline > datetime.now(timezone.utc))
    )

    normalized_search = search.strip() if search else ""

    if normalized_search:
        pattern = f"%{normalized_search}%"
        query = query.filter(
            or_(
                Job.title.ilike(pattern),
                Job.category.ilike(pattern),
                Job.description.ilike(pattern),
            )
        )

    if category:
        query = query.filter(Job.category == category)

    allowed_location_types = {"remote", "on_site", "hybrid"}

    if location_type:
        if location_type not in allowed_location_types:
            raise_core_error("invalid_location_type")

        query = query.filter(Job.location_type == location_type)

    if location and location.strip():
        normalized_location = location.strip()

        if location_type == "remote":
            pass
        else:
            query = query.filter(
                Job.location.ilike(f"%{normalized_location}%"),
                Job.location_type.in_(["on_site", "hybrid"]),
            )
    if budget_type:
        query = query.filter(Job.budget_type == budget_type)

    if min_budget is not None:
        query = query.filter(Job.budget_amount >= min_budget)

    if max_budget is not None:
        query = query.filter(Job.budget_amount <= max_budget)
    total = query.count()
    rows = (
        query.order_by(Job.created_at.desc(), Job.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse[JobSearchItemResponse](
        items=[build_job_search_item(job, client) for job, client in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )


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

    replacement_by_source_id = {
        source_job_id: replacement_job_id
        for replacement_job_id, source_job_id in db.query(
            Job.id,
            Job.source_job_id,
        )
        .filter(
            Job.client_id == client_id,
            Job.source_job_id.isnot(None),
        )
        .all()
    }

    return [
        JobSummaryResponse(
            id=job.id,
            replacement_job_id=replacement_by_source_id.get(job.id),
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


def _get_accepted_job_application(
    db: Session,
    job_id: int,
) -> tuple[Job, Application]:
    row = db.execute(
        select(Job, Application)
        .join(Application, Application.job_id == Job.id)
        .where(
            Job.id == job_id,
            Application.status == "accepted",
        )
        .with_for_update()
    ).one_or_none()

    if row is None:
        raise_core_error("job_not_found")

    return row


def mark_job_done(db: Session, job_id: int, current_user: Profile) -> JobResponse:
    job, application = _get_accepted_job_application(db, job_id)

    if current_user.role != "contractor":
        raise_core_error("forbidden")
    if application.contractor_id != current_user.user_id:
        raise_core_error("forbidden")
    if job.status != "in_progress":
        raise_core_error("job_cannot_be_marked_done")

    job.status = "done_by_contractor"

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return JobResponse.model_validate(job)


async def mark_job_completed(
    db: Session,
    job_id: int,
    current_user: Profile,
) -> JobResponse:
    job, application = _get_accepted_job_application(db, job_id)

    if current_user.role != "client" or job.client_id != current_user.user_id:
        raise_core_error("forbidden")
    if job.status != "done_by_contractor":
        raise_core_error("job_cannot_be_completed")

    await update_contract_status_for_job(job.id, "complete")
    # await create_pending_payment(job.id, application.id)  # TODO
    job.status = "completed_by_client"

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return JobResponse.model_validate(job)


async def mark_job_incomplete(
    db: Session,
    job_id: int,
    current_user: Profile,
) -> JobResponse:
    job, _application = _get_accepted_job_application(db, job_id)

    if current_user.role != "client" or job.client_id != current_user.user_id:
        raise_core_error("forbidden")
    if job.status != "done_by_contractor":
        raise_core_error("job_cannot_be_marked_incomplete")

    await update_contract_status_for_job(job.id, "cancel")
    job.status = "incomplete"

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return JobResponse.model_validate(job)
