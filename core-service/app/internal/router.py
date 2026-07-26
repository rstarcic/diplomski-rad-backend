from app.dependencies import _verify_internal
from app.jobs.models import Job
from app.profiles.models import Profile
from app.profiles.schemas import InternalContractorProfileResponse
from database import get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

load_dotenv(override=False)


router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(_verify_internal)],
)


@router.get(
    "/profiles/{user_id}/contractor",
    response_model=InternalContractorProfileResponse,
)
def get_contractor_profile_for_internal_service(
    user_id: int,
    db: Session = Depends(get_db),
):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user_id, Profile.role == "contractor")
        .first()
    )
    if profile is None:
        raise HTTPException(404, detail="Contractor profile not found.")
    return profile


@router.patch("/jobs/{job_id}/contract-activated")
def activate_job_from_contract(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found.")

    if job.status == "in_progress":
        return {"job_id": job.id, "status": job.status}
    if job.status != "awaiting_contract":
        raise HTTPException(
            409,
            detail=f"Job cannot be activated from status '{job.status}'.",
        )

    job.status = "in_progress"
    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return {"job_id": job.id, "status": job.status}
    return {"job_id": job.id, "status": job.status}
