import os

from app.dependencies import get_current_user
from app.profiles.models import Profile
from app.profiles.schemas import (
    ProfileCreate,
    ProfilePageResponse,
    ProfileResponse,
)
from app.profiles.service import (
    create_profile_if_not_exists,
    get_my_profile_page,
    update_my_profile_page_from_request,
)
from database import get_db
from errors import raise_core_error
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

router = APIRouter()

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _verify_internal(x_internal_secret: str = Header(...)):
    if INTERNAL_SECRET and x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/init", response_model=ProfileResponse, status_code=201)
def init_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_internal),
):
    return create_profile_if_not_exists(db, data)


@router.get("/me", response_model=ProfilePageResponse)
def get_my_profile_page_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    profile_page = get_my_profile_page(db, current_user.user_id)

    if not profile_page:
        raise_core_error("profile_not_found")

    return profile_page


@router.put("/me", response_model=ProfilePageResponse)
async def update_my_profile_page_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    profile_page = await update_my_profile_page_from_request(
        db=db,
        user_id=current_user.user_id,
        request=request,
    )

    if profile_page is None:
        raise_core_error("profile_not_found")

    return profile_page
