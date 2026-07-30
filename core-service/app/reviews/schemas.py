from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    comment: str = Field(min_length=10, max_length=1000)
    communication_rating: float = Field(ge=1, le=5)
    clarity_rating: float = Field(ge=1, le=5)
    reliability_rating: float = Field(ge=1, le=5)
    collaboration_rating: float = Field(ge=1, le=5)


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


class ReviewCreateResponse(ReviewItemResponse):
    job_id: int
    target_id: int
    target_type: str


class TargetReviewsResponse(BaseModel):
    target_type: str
    target_id: int
    summary: ReviewSummaryResponse
    items: list[ReviewItemResponse]
