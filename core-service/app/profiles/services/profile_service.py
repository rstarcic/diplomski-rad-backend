from app.profiles.models import Profile
from app.profiles.schemas import (
    ClientProfilePageResponse,
    ContractorProfilePageResponse,
    ProfileCreate,
    ProfilePageResponse,
    ProfilePageUpdate,
)
from app.profiles.services.profile_repository import (
    _replace_contractor_portfolio,
    _replace_contractor_skills,
    get_portfolio_for_contractor,
    get_profile_by_user_id,
    get_skills_for_contractor,
)
from app.profiles.services.profile_update_parser import profile_update_from_request
from app.reviews.schemas import TargetReviewsResponse
from app.reviews.service import get_reviews_for_target
from fastapi import Request
from sqlalchemy.orm import Session


def _compute_profile_completed(profile: Profile) -> bool:
    return all(
        [
            profile.full_name,
            profile.email,
            profile.phone,
            profile.country,
            profile.city,
            profile.about,
            profile.profile_picture or profile.profile_picture_blob,
        ]
    )


def get_client_profile_page(
    profile: Profile,
    reviews: TargetReviewsResponse,
) -> ClientProfilePageResponse:
    return ClientProfilePageResponse(
        profile=profile,
        reviews=reviews,
    )


def get_contractor_profile_page(
    db: Session,
    profile: Profile,
    reviews: TargetReviewsResponse,
) -> ContractorProfilePageResponse:
    return ContractorProfilePageResponse(
        profile=profile,
        reviews=reviews,
        skills=get_skills_for_contractor(db, profile.user_id),
        portfolio=get_portfolio_for_contractor(db, profile.user_id),
    )


def create_profile_if_not_exists(db: Session, data: ProfileCreate) -> Profile:
    existing = get_profile_by_user_id(db, data.user_id)
    if existing:
        return existing

    profile = Profile(**data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_my_profile_page(
    db: Session,
    user_id: int,
) -> ProfilePageResponse | None:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return None

    reviews = get_reviews_for_target(
        db=db,
        target_type=profile.role,
        target_id=profile.user_id,
    )

    if profile.role == "contractor":
        return get_contractor_profile_page(db, profile, reviews)

    return get_client_profile_page(profile, reviews)


def update_my_profile_page(
    db: Session,
    user_id: int,
    data: ProfilePageUpdate,
    profile_picture_blob: bytes | None = None,
    profile_picture_content_type: str | None = None,
) -> ProfilePageResponse | None:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return None

    profile_updates = data.profile.model_dump(exclude_unset=True)

    for field, value in profile_updates.items():
        setattr(profile, field, value)

    if profile_picture_blob is not None:
        profile.profile_picture_blob = profile_picture_blob
        profile.profile_picture_content_type = profile_picture_content_type

    if profile.role == "contractor":
        if data.skills is not None:
            _replace_contractor_skills(db, user_id, data.skills)

        if data.portfolio is not None:
            _replace_contractor_portfolio(db, user_id, data.portfolio)

    profile.profile_completed = _compute_profile_completed(profile)

    db.commit()
    db.refresh(profile)

    return get_my_profile_page(db, user_id)


async def update_my_profile_page_from_request(
    db: Session,
    user_id: int,
    request: Request,
) -> ProfilePageResponse | None:
    data, profile_picture_blob, profile_picture_content_type = (
        await profile_update_from_request(request)
    )

    return update_my_profile_page(
        db=db,
        user_id=user_id,
        data=data,
        profile_picture_blob=profile_picture_blob,
        profile_picture_content_type=profile_picture_content_type,
    )
