from app.profiles.models import ContractorSkill, PortfolioItem, Profile
from app.profiles.schemas import PortfolioItemUpdate, SkillUpdate
from sqlalchemy import delete, select
from sqlalchemy.orm import Session


def get_profile_by_user_id(
    db: Session,
    user_id: int,
) -> Profile | None:
    return db.scalars(select(Profile).where(Profile.user_id == user_id)).first()


def get_contractor_profile_by_user_id(
    db: Session,
    user_id: int,
) -> Profile | None:
    return db.scalars(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.role == "contractor",
        )
    ).first()


def get_client_profile_by_user_id(
    db: Session,
    user_id: int,
) -> Profile | None:
    return db.scalars(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.role == "client",
        )
    ).first()


def get_skills_for_contractor(
    db: Session,
    user_id: int,
) -> list[ContractorSkill]:
    if not get_contractor_profile_by_user_id(db, user_id):
        return []

    return list(
        db.scalars(
            select(ContractorSkill)
            .where(ContractorSkill.contractor_id == user_id)
            .order_by(ContractorSkill.name.asc())
        ).all()
    )


def get_portfolio_for_contractor(
    db: Session,
    user_id: int,
) -> list[PortfolioItem]:
    if not get_contractor_profile_by_user_id(db, user_id):
        return []

    return list(
        db.scalars(
            select(PortfolioItem)
            .where(PortfolioItem.contractor_id == user_id)
            .order_by(PortfolioItem.created_at.desc())
        ).all()
    )


def _replace_contractor_skills(
    db: Session,
    user_id: int,
    skills: list[SkillUpdate],
) -> None:
    db.execute(delete(ContractorSkill).where(ContractorSkill.contractor_id == user_id))

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
    db.execute(delete(PortfolioItem).where(PortfolioItem.contractor_id == user_id))

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
