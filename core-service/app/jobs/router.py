from app.dependencies import get_current_user
from app.integrations.client import get_payment_profile_status
from app.jobs.schemas import (
    JobCreate,
    JobDetailsPageResponse,
    JobFilterOptionsResponse,
    JobResponse,
    JobSearchItemResponse,
    JobSummaryResponse,
    JobUpdate,
)
from app.jobs.service import (
    create_job,
    get_job_by_id,
    get_job_details,
    get_job_filter_options,
    get_my_jobs,
    get_open_jobs,
    mark_job_completed,
    mark_job_done,
    mark_job_incomplete,
    update_job,
)
from app.pagination import PaginatedResponse, PaginationParams
from app.profiles.models import Profile
from database import get_db
from errors import raise_core_error
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.patch("/{job_id}/done", response_model=JobResponse)
def mark_job_done_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return mark_job_done(db, job_id, current_user)


@router.patch("/{job_id}/complete", response_model=JobResponse)
async def mark_job_completed_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return await mark_job_completed(db, job_id, current_user)


@router.patch("/{job_id}/incomplete", response_model=JobResponse)
async def mark_job_incomplete_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return await mark_job_incomplete(db, job_id, current_user)


@router.get("/", response_model=PaginatedResponse[JobSearchItemResponse])
def get_open_jobs_endpoint(
    search: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None),
    location: str | None = Query(default=None),
    location_type: str | None = Query(default=None),
    budget_type: str | None = Query(default=None),
    min_budget: float | None = Query(default=None, ge=0),
    max_budget: float | None = Query(default=None, ge=0),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    return get_open_jobs(
        db=db,
        search=search,
        category=category,
        location=location,
        location_type=location_type,
        budget_type=budget_type,
        min_budget=min_budget,
        max_budget=max_budget,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/filter-options", response_model=JobFilterOptionsResponse)
def get_filter_options_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    return get_job_filter_options(db)


@router.post("/", response_model=JobResponse, status_code=201)
async def post_job_endpoint(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    if not current_user.profile_completed:
        raise_core_error("profile_completion_required")

    payment_status = await get_payment_profile_status(current_user.user_id)
    if payment_status is None or not payment_status.payment_setup_completed:
        raise_core_error("payment_setup_required")

    return create_job(db, current_user.user_id, data)


@router.get("/me", response_model=list[JobSummaryResponse], status_code=200)
async def get_my_jobs_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    return await get_my_jobs(db, current_user.user_id)


@router.get("/{job_id}/details", response_model=JobDetailsPageResponse)
def get_job_details_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    details = get_job_details(
        db=db,
        job_id=job_id,
        contractor_id=current_user.user_id,
    )

    if details is None:
        raise_core_error("job_not_found")

    return details


@router.get("/{job_id}", response_model=JobResponse, status_code=200)
def get_job_by_id_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    job = get_job_by_id(db, current_user.user_id, job_id)

    if job is None:
        raise_core_error("job_not_found")

    return job


@router.put("/{job_id}", response_model=JobResponse)
def update_job_endpoint(
    job_id: int,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("only_clients_can_update_jobs")

    job = update_job(
        db=db,
        client_id=current_user.user_id,
        job_id=job_id,
        data=data,
    )

    if job is None:
        raise_core_error("job_not_found")

    return job
