from app.profiles.schemas import (
    ContractorPublicPortfolioItem,
    ContractorPublicProfile,
    ContractorPublicProfileResponse,
    ContractorPublicSkill,
)
from app.profiles.services.profile_repository import (
    get_contractor_profile_by_user_id,
    get_portfolio_for_contractor,
    get_skills_for_contractor,
)
from app.profiles.services.stats_service import (
    build_contractor_public_stats,
    count_active_contracts_for_contractor,
    count_completed_jobs_for_contractor,
    get_average_response_time_for_contractor,
)
from app.reviews.service import get_reviews_for_target
from sqlalchemy.orm import Session


def get_contractor_public_profile(
    db: Session,
    contractor_id: int,
) -> ContractorPublicProfileResponse | None:
    contractor = get_contractor_profile_by_user_id(db, contractor_id)

    if contractor is None:
        return None

    reviews = get_reviews_for_target(
        db=db,
        target_type="contractor",
        target_id=contractor.user_id,
    )

    skills = get_skills_for_contractor(db, contractor.user_id)
    portfolio = get_portfolio_for_contractor(db, contractor.user_id)

    completed_jobs = count_completed_jobs_for_contractor(db, contractor.user_id)
    active_contracts = count_active_contracts_for_contractor(db, contractor.user_id)
    average_response_time = get_average_response_time_for_contractor(
        db,
        contractor.user_id,
    )
    stats = build_contractor_public_stats(
        contractor=contractor,
        completed_jobs=completed_jobs,
        active_contracts=active_contracts,
        average_response_time=average_response_time,
        skills_count=len(skills),
        portfolio_count=len(portfolio),
    )

    return ContractorPublicProfileResponse(
        profile=ContractorPublicProfile(
            user_id=contractor.user_id,
            full_name=contractor.full_name,
            profile_picture=contractor.display_profile_picture,
            email=contractor.email,
            phone=contractor.phone,
            city=contractor.city,
            country=contractor.country,
            created_at=contractor.created_at,
            about=contractor.about,
        ),
        portfolio=[
            ContractorPublicPortfolioItem(
                id=item.id,
                title=item.title,
                description=item.description,
                project_url=item.project_url,
                image_url=item.image_url,
            )
            for item in portfolio
        ],
        skills=[
            ContractorPublicSkill(
                id=skill.id,
                name=skill.name,
            )
            for skill in skills
        ],
        stats=stats,
        reviews=reviews,
    )
