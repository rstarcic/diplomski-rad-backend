from app.dependencies import get_current_user
from app.jobs.schemas import (
    JobCreate,
    JobResponse,
    JobSearchItemResponse,
    JobSummaryResponse,
    JobUpdate,
)
from app.jobs.service import (
    create_job,
    get_job_by_id,
    get_my_jobs,
    get_open_jobs,
    update_job,
)
from app.profiles.models import Profile
from database import get_db
from errors import raise_core_error
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=list[JobSearchItemResponse])
def get_open_jobs_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    return get_open_jobs(db)


@router.post("/", response_model=JobResponse, status_code=201)
def post_job_endpoint(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    return create_job(db, current_user.user_id, data)


@router.get("/me", response_model=list[JobSummaryResponse], status_code=200)
def get_my_jobs_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    return get_my_jobs(db, current_user.user_id)


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
