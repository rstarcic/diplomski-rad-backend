from app.dependencies import _verify_internal, get_current_user
from app.profiles.models import Profile
from app.profiles.schemas import (
    ClientPublicProfileResponse,
    ContractorPublicProfileResponse,
    ProfileCreate,
    ProfilePageResponse,
    ProfileResponse,
)
from app.profiles.services.profile_service import (
    create_profile_if_not_exists,
    get_my_profile_page,
    update_my_profile_page_from_request,
)
from app.profiles.services.public_profile_service import (
    get_client_public_profile,
    get_contractor_public_profile,
)
from database import get_db
from errors import raise_core_error
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

router = APIRouter()


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

    if profile_page is None:
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


@router.get(
    "/contractors/{contractor_id}",
    response_model=ContractorPublicProfileResponse,
)
def get_contractor_public_profile_endpoint(
    contractor_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    contractor_profile = get_contractor_public_profile(db, contractor_id)

    if contractor_profile is None:
        raise_core_error("profile_not_found")

    return contractor_profile


@router.get(
    "/clients/{client_id}",
    response_model=ClientPublicProfileResponse,
)
def get_client_public_profile_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    client_profile = get_client_public_profile(db, client_id)

    if client_profile is None:
        raise_core_error("profile_not_found")

    return client_profile
