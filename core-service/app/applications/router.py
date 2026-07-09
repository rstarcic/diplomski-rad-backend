from app.applications.schemas import (
    JobApplicationDetailResponse,
    JobApplicationItemResponse,
)
from app.applications.service import get_job_application_detail, get_job_applications
from app.dependencies import get_current_user
from app.profiles.models import Profile
from database import get_db
from errors import raise_core_error
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/jobs/{job_id}/applications", response_model=list[JobApplicationItemResponse]
)
def get_job_applications_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    applications = get_job_applications(
        db=db,
        client_id=current_user.user_id,
        job_id=job_id,
    )

    if applications is None:
        raise_core_error("job_not_found")

    return applications


@router.get(
    "/jobs/{job_id}/applications/{application_id}",
    response_model=JobApplicationDetailResponse,
)
def get_job_application_detail_endpoint(
    job_id: int,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    application = get_job_application_detail(
        db=db,
        client_id=current_user.user_id,
        job_id=job_id,
        application_id=application_id,
    )

    if application is None:
        raise_core_error("application_not_found")

    return application
