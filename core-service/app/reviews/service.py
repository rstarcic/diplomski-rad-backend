from app.applications.models import Application
from app.integrations.client import get_payment_summary
from app.jobs.models import Job
from app.profiles.models import Profile
from app.reviews.models import Review
from app.reviews.schemas import (
    ReviewCreate,
    ReviewCreateResponse,
    ReviewerResponse,
    ReviewItemResponse,
    ReviewRatingsResponse,
    ReviewSummaryResponse,
    TargetReviewsResponse,
)
from errors import raise_core_error
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload


def _round_to_half(value: float) -> float:
    return round(value * 2) / 2


def _calculate_review_average(review: Review) -> float:
    return (
        review.communication_rating
        + review.clarity_rating
        + review.reliability_rating
        + review.collaboration_rating
    ) / 4


def _build_empty_summary() -> ReviewSummaryResponse:
    empty_ratings = ReviewRatingsResponse(
        communication_rating=0,
        clarity_rating=0,
        reliability_rating=0,
        collaboration_rating=0,
    )

    return ReviewSummaryResponse(
        total_reviews=0,
        raw_overall_rating=0,
        overall_rating=0,
        ratings=empty_ratings,
    )


def _build_review_summary(reviews: list[Review]) -> ReviewSummaryResponse:
    total_reviews = len(reviews)
    if total_reviews == 0:
        return _build_empty_summary()

    communication_rating = (
        sum(review.communication_rating for review in reviews) / total_reviews
    )
    clarity_rating = sum(review.clarity_rating for review in reviews) / total_reviews
    reliability_rating = (
        sum(review.reliability_rating for review in reviews) / total_reviews
    )
    collaboration_rating = (
        sum(review.collaboration_rating for review in reviews) / total_reviews
    )
    raw_overall_rating = (
        sum(_calculate_review_average(review) for review in reviews) / total_reviews
    )

    return ReviewSummaryResponse(
        total_reviews=total_reviews,
        raw_overall_rating=raw_overall_rating,
        overall_rating=_round_to_half(raw_overall_rating),
        ratings=ReviewRatingsResponse(
            communication_rating=communication_rating,
            clarity_rating=clarity_rating,
            reliability_rating=reliability_rating,
            collaboration_rating=collaboration_rating,
        ),
    )


def _build_review_item(review: Review) -> ReviewItemResponse:
    raw_overall_rating = _calculate_review_average(review)

    return ReviewItemResponse(
        id=review.id,
        comment=review.comment,
        created_at=review.created_at,
        reviewer=ReviewerResponse(
            user_id=review.reviewer.user_id,
            full_name=review.reviewer.full_name,
            profile_picture=review.reviewer.display_profile_picture,
        ),
        raw_overall_rating=raw_overall_rating,
        overall_rating=_round_to_half(raw_overall_rating),
        ratings=ReviewRatingsResponse(
            communication_rating=review.communication_rating,
            clarity_rating=review.clarity_rating,
            reliability_rating=review.reliability_rating,
            collaboration_rating=review.collaboration_rating,
        ),
    )


async def create_job_review(
    db: Session,
    job_id: int,
    current_user: Profile,
    data: ReviewCreate,
) -> ReviewCreateResponse:
    row = db.execute(
        select(Job, Application)
        .join(Application, Application.job_id == Job.id)
        .where(
            Job.id == job_id,
            Application.status == "accepted",
        )
    ).one_or_none()

    if row is None:
        job_exists = db.scalar(select(Job.id).where(Job.id == job_id))
        if job_exists is None:
            raise_core_error("job_not_found")
        raise_core_error("review_not_available")

    job, application = row

    if (
        current_user.role == "client"
        and current_user.user_id == job.client_id
    ):
        target_id = application.contractor_id
        target_type = "contractor"
    elif (
        current_user.role == "contractor"
        and current_user.user_id == application.contractor_id
    ):
        target_id = job.client_id
        target_type = "client"
    else:
        raise_core_error("forbidden")

    payment = await get_payment_summary(application.id)
    if payment is None or payment.status != "paid":
        raise_core_error("review_payment_required")

    existing_review = db.scalar(
        select(Review.id).where(
            Review.job_id == job_id,
            Review.reviewer_id == current_user.user_id,
        )
    )
    if existing_review is not None:
        raise_core_error("review_already_submitted")

    review = Review(
        job_id=job_id,
        reviewer_id=current_user.user_id,
        target_id=target_id,
        target_type=target_type,
        comment=data.comment.strip(),
        communication_rating=data.communication_rating,
        clarity_rating=data.clarity_rating,
        reliability_rating=data.reliability_rating,
        collaboration_rating=data.collaboration_rating,
    )

    try:
        db.add(review)
        db.commit()
        db.refresh(review)
    except IntegrityError:
        db.rollback()
        raise_core_error("review_already_submitted")
    except Exception:
        db.rollback()
        raise

    item = _build_review_item(review)
    return ReviewCreateResponse(
        **item.model_dump(),
        job_id=job_id,
        target_id=target_id,
        target_type=target_type,
    )


def get_reviews_for_target(
    db: Session,
    target_type: str,
    target_id: int,
) -> TargetReviewsResponse:
    reviews = list(
        db.scalars(
            select(Review)
            .options(joinedload(Review.reviewer))
            .where(
                Review.target_type == target_type,
                Review.target_id == target_id,
            )
            .order_by(Review.created_at.desc())
        ).all()
    )

    return TargetReviewsResponse(
        target_type=target_type,
        target_id=target_id,
        summary=_build_review_summary(reviews),
        items=[_build_review_item(review) for review in reviews],
    )
