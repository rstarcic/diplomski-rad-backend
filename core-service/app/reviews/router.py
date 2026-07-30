from app.dependencies import get_current_user
from app.profiles.models import Profile
from app.reviews.schemas import ReviewCreate, ReviewCreateResponse
from app.reviews.service import create_job_review
from database import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/jobs/{job_id}/review",
    response_model=ReviewCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job_review_endpoint(
    job_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return await create_job_review(
        db=db,
        job_id=job_id,
        current_user=current_user,
        data=data,
    )
