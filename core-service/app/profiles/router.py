import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import raise_core_error
from app.profiles.schemas import ProfileCreate, ProfileResponse, ProfileUpdate
from app.profiles.service import create_profile_if_not_exists, get_profile, update_profile

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


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile_endpoint(user_id: int, db: Session = Depends(get_db)):
    profile = get_profile(db, user_id)
    if not profile:
        raise_core_error("profile_not_found")
    return profile


@router.patch("/{user_id}", response_model=ProfileResponse)
def update_profile_endpoint(
    user_id: int, data: ProfileUpdate, db: Session = Depends(get_db)
):
    profile = update_profile(db, user_id, data)
    if not profile:
        raise_core_error("profile_not_found")
    return profile
