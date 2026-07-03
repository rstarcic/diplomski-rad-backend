from datetime import datetime

from pydantic import BaseModel


class ReviewerResponse(BaseModel):
    user_id: int
    full_name: str | None = None
    profile_picture: str | None = None

    model_config = {"from_attributes": True}


class ReviewRatingsResponse(BaseModel):
    communication_rating: float
    clarity_rating: float
    reliability_rating: float
    collaboration_rating: float


class ReviewSummaryResponse(BaseModel):
    total_reviews: int
    overall_rating: float
    raw_overall_rating: float
    ratings: ReviewRatingsResponse


class ReviewItemResponse(BaseModel):
    id: int
    comment: str
    created_at: datetime
    reviewer: ReviewerResponse
    raw_overall_rating: float
    overall_rating: float
    ratings: ReviewRatingsResponse


class TargetReviewsResponse(BaseModel):
    target_type: str
    target_id: int
    summary: ReviewSummaryResponse
    items: list[ReviewItemResponse]
