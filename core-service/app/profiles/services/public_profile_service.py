from app.profiles.schemas import (
    ClientPublicProfile,
    ClientPublicProfileResponse,
    ContractorPublicPortfolioItem,
    ContractorPublicProfile,
    ContractorPublicProfileResponse,
    ContractorPublicSkill,
)
from app.profiles.services.profile_repository import (
    get_client_profile_by_user_id,
    get_contractor_profile_by_user_id,
    get_portfolio_for_contractor,
    get_skills_for_contractor,
)
from app.profiles.services.stats_service import (
    build_client_public_stats,
    build_contractor_public_stats,
    count_active_jobs_for_client,
    count_active_contracts_for_contractor,
    count_completed_jobs_for_client,
    count_completed_jobs_for_contractor,
    count_jobs_posted_by_client,
    get_average_response_time_for_client,
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


def get_client_public_profile(
    db: Session,
    client_id: int,
) -> ClientPublicProfileResponse | None:
    client = get_client_profile_by_user_id(db, client_id)

    if client is None:
        return None

    reviews = get_reviews_for_target(
        db=db,
        target_type="client",
        target_id=client.user_id,
    )

    jobs_posted = count_jobs_posted_by_client(db, client.user_id)
    completed_jobs = count_completed_jobs_for_client(db, client.user_id)
    active_jobs = count_active_jobs_for_client(db, client.user_id)
    average_response_time = get_average_response_time_for_client(
        db,
        client.user_id,
    )
    stats = build_client_public_stats(
        jobs_posted=jobs_posted,
        jobs_completed=completed_jobs,
        active_jobs=active_jobs,
        average_response_time=average_response_time,
    )

    return ClientPublicProfileResponse(
        profile=ClientPublicProfile(
            user_id=client.user_id,
            full_name=client.full_name,
            profile_picture=client.display_profile_picture,
            email=client.email,
            phone=client.phone,
            city=client.city,
            country=client.country,
            created_at=client.created_at,
            about=client.about,
        ),
        stats=stats,
        reviews=reviews,
    )
