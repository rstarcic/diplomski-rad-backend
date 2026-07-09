from datetime import datetime
from typing import Literal

from app.negotiations.schemas import NegotiationEditResponse, NegotiationSummaryResponse
from app.profiles.schemas import ContractorPublicProfile
from app.reviews.schemas import TargetReviewsResponse
from pydantic import BaseModel

ApplicationStatus = Literal[
    "pending",
    "negotiating",
    "accepted",
    "rejected",
    "withdrawn",
]


class ApplicationContractorPreview(BaseModel):
    user_id: int
    full_name: str | None = None
    profile_picture: str | None = None
    city: str | None = None
    country: str | None = None


class ApplicationSummary(BaseModel):
    id: int
    status: ApplicationStatus
    cover_letter: str


class ApplicationSummaryDetail(ApplicationSummary):
    created_at: datetime


class ApplicationJobSummary(BaseModel):
    id: int
    title: str


class JobApplicationItemResponse(BaseModel):
    contractor: ApplicationContractorPreview
    application: ApplicationSummary
    job: ApplicationJobSummary


class JobApplicationDetailResponse(BaseModel):
    application: ApplicationSummaryDetail
    contractor: ContractorPublicProfile
    reviews: TargetReviewsResponse
    negotiation: NegotiationSummaryResponse | None = None
    negotiationUpdates: list[NegotiationEditResponse]
    contract: None = None  # TODO
    payment: None = None  # TODO
