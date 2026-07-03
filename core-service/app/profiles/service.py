import json

from app.profiles.models import ContractorSkill, PortfolioItem, Profile
from app.profiles.schemas import (ClientProfilePageResponse,
                                  ContractorProfilePageResponse,
                                  PortfolioItemUpdate, ProfileCreate,
                                  ProfilePageResponse, ProfilePageUpdate,
                                  ProfileUpdate, SkillUpdate)
from app.reviews.schemas import TargetReviewsResponse
from app.reviews.service import get_reviews_for_target
from errors import raise_core_error
from fastapi import Request
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

PROFILE_PICTURE_FIELDS = (
    "profile_picture",
    "profilePicture",
    "image",
    "avatar",
    "file",
)


def _json_form_field(value: object) -> object:
    if value is None or value == "":
        return None

    if not isinstance(value, str):
        raise_core_error("invalid_multipart_json")

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        raise_core_error("invalid_multipart_json")


def _profile_payload_from_form(form) -> dict:
    payload = {}

    for field in ProfileUpdate.model_fields:
        value = form.get(field)
        if isinstance(value, str):
            payload[field] = value

    return payload


async def _read_profile_picture_blob(file: UploadFile) -> tuple[bytes, str]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise_core_error("profile_picture_invalid_type")

    content = await file.read()
    if not content:
        raise_core_error("profile_picture_empty")

    return content, file.content_type


async def _profile_picture_from_form(
    form,
) -> tuple[bytes | None, str | None, str | None]:
    for field_name in PROFILE_PICTURE_FIELDS:
        value = form.get(field_name)

        if isinstance(value, UploadFile):
            blob, content_type = await _read_profile_picture_blob(value)
            return blob, content_type, None

        if isinstance(value, str) and value:
            return None, None, value

    return None, None, None


async def _profile_update_from_multipart(
    request: Request,
) -> tuple[ProfilePageUpdate, bytes | None, str | None]:
    form = await request.form()

    payload = _profile_payload_from_form(form)
    profile_picture_blob, profile_picture_content_type, profile_picture_url = (
        await _profile_picture_from_form(form)
    )

    if profile_picture_url:
        payload["profile_picture"] = profile_picture_url

    data = ProfilePageUpdate(
        profile=ProfileUpdate(**payload),
        skills=_json_form_field(form.get("skills")),
        portfolio=_json_form_field(form.get("portfolio")),
    )

    return data, profile_picture_blob, profile_picture_content_type


async def profile_update_from_request(
    request: Request,
) -> tuple[ProfilePageUpdate, bytes | None, str | None]:
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        return await _profile_update_from_multipart(request)

    return ProfilePageUpdate.model_validate(await request.json()), None, None


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


def _get_profile_by_user_id(db: Session, user_id: int) -> Profile | None:
    return db.query(Profile).filter(Profile.user_id == user_id).first()


def _get_contractor_profile_by_user_id(db: Session, user_id: int) -> Profile | None:
    return (
        db.query(Profile)
        .filter(Profile.user_id == user_id, Profile.role == "contractor")
        .first()
    )


def _get_skills_for_contractor(db: Session, user_id: int) -> list[ContractorSkill]:
    if not _get_contractor_profile_by_user_id(db, user_id):
        return []

    return (
        db.query(ContractorSkill)
        .filter(ContractorSkill.contractor_id == user_id)
        .order_by(ContractorSkill.name.asc())
        .all()
    )


def _get_portfolio_for_contractor(db: Session, user_id: int) -> list[PortfolioItem]:
    if not _get_contractor_profile_by_user_id(db, user_id):
        return []

    return (
        db.query(PortfolioItem)
        .filter(PortfolioItem.contractor_id == user_id)
        .order_by(PortfolioItem.created_at.desc())
        .all()
    )


def _replace_contractor_skills(
    db: Session,
    user_id: int,
    skills: list[SkillUpdate],
) -> None:
    db.query(ContractorSkill).filter(ContractorSkill.contractor_id == user_id).delete()

    for skill in skills:
        db.add(
            ContractorSkill(
                contractor_id=user_id,
                name=skill.name,
            )
        )


def _replace_contractor_portfolio(
    db: Session,
    user_id: int,
    portfolio: list[PortfolioItemUpdate],
) -> None:
    db.query(PortfolioItem).filter(PortfolioItem.contractor_id == user_id).delete()

    for item in portfolio:
        db.add(
            PortfolioItem(
                contractor_id=user_id,
                title=item.title,
                description=item.description,
                image_url=item.image_url,
                project_url=item.project_url,
            )
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
        skills=_get_skills_for_contractor(db, profile.user_id),
        portfolio=_get_portfolio_for_contractor(db, profile.user_id),
    )


def create_profile_if_not_exists(db: Session, data: ProfileCreate) -> Profile:
    existing = _get_profile_by_user_id(db, data.user_id)
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
    profile = _get_profile_by_user_id(db, user_id)
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
    profile = _get_profile_by_user_id(db, user_id)
    if not profile:
        return None

    for field, value in data.profile.model_dump(exclude_unset=True).items():
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
