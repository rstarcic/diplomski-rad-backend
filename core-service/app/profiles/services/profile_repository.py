from app.profiles.models import ContractorSkill, PortfolioItem, Profile
from app.profiles.schemas import PortfolioItemUpdate, SkillUpdate
from sqlalchemy.orm import Session


def get_profile_by_user_id(db: Session, user_id: int) -> Profile | None:
    return db.query(Profile).filter(Profile.user_id == user_id).first()


def get_contractor_profile_by_user_id(db: Session, user_id: int) -> Profile | None:
    return (
        db.query(Profile)
        .filter(Profile.user_id == user_id, Profile.role == "contractor")
        .first()
    )


def get_client_profile_by_user_id(db: Session, user_id: int) -> Profile | None:
    return (
        db.query(Profile)
        .filter(Profile.user_id == user_id, Profile.role == "client")
        .first()
    )


def get_skills_for_contractor(db: Session, user_id: int) -> list[ContractorSkill]:
    if not get_contractor_profile_by_user_id(db, user_id):
        return []

    return (
        db.query(ContractorSkill)
        .filter(ContractorSkill.contractor_id == user_id)
        .order_by(ContractorSkill.name.asc())
        .all()
    )


def get_portfolio_for_contractor(db: Session, user_id: int) -> list[PortfolioItem]:
    if not get_contractor_profile_by_user_id(db, user_id):
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
