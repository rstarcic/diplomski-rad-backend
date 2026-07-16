import os
import secrets

from app.jobs.models import Job
from database import get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

load_dotenv(override=False)

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")
router = APIRouter(prefix="/internal", tags=["internal"])


def verify_internal(x_internal_secret: str = Header(...)) -> None:
    if not INTERNAL_SECRET:
        raise HTTPException(503, detail="Internal API authentication is not configured.")
    if not secrets.compare_digest(x_internal_secret, INTERNAL_SECRET):
        raise HTTPException(403, detail="Forbidden")


@router.patch(
    "/jobs/{job_id}/contract-activated",
    dependencies=[Depends(verify_internal)],
)
def activate_job_from_contract(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, detail="Job not found.")

    # Idempotent: a repeated callback has the same result.
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
