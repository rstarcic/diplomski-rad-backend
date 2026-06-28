from sqlalchemy.orm import Session

from app.profiles.models import Profile
from app.profiles.schemas import ProfileCreate, ProfileUpdate


def _compute_profile_completed(profile: Profile) -> bool:
    return all([
        profile.full_name,
        profile.email,
        profile.phone,
        profile.country,
        profile.city,
        profile.about,
        profile.profile_picture,
    ])


def create_profile_if_not_exists(db: Session, data: ProfileCreate) -> Profile:
    existing = db.query(Profile).filter(Profile.user_id == data.user_id).first()
    if existing:
        return existing

    profile = Profile(**data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, user_id: int) -> Profile | None:
    return db.query(Profile).filter(Profile.user_id == user_id).first()


def update_profile(db: Session, user_id: int, data: ProfileUpdate) -> Profile | None:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    profile.profile_completed = _compute_profile_completed(profile)
    db.commit()
    db.refresh(profile)
    return profile
