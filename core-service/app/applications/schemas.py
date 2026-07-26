from datetime import datetime
from typing import Literal

from app.integrations.schemas import ContractSummary, PaymentSummary
from app.jobs.schemas import JobResponse
from app.negotiations.schemas import NegotiationEditResponse, NegotiationSummaryResponse
from app.profiles.schemas import ClientPublicProfile, ContractorPublicProfile
from app.reviews.schemas import TargetReviewsResponse
from pydantic import BaseModel, ConfigDict, Field

ApplicationStatus = Literal[
    "pending",
    "selected",
    "accepted",
    "rejected",
    "withdrawn",
]

# Application creation by contractor


class ApplicationCreate(BaseModel):
    cover_letter: str = Field(..., min_length=1, max_length=5000)


class ApplicationCreateResponse(BaseModel):
    id: int
    job_id: int
    contractor_id: int
    cover_letter: str
    status: ApplicationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Application decision by client


class ApplicationDecision(BaseModel):
    decision: Literal["selected", "rejected"]


class ApplicationDecisionResponse(BaseModel):
    id: int
    status: ApplicationStatus


# Applications list seen by client on job applications page


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


# Single application details seen by client


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
    negotiation_updates: list[NegotiationEditResponse]
    contract: ContractSummary | None = None
    payment: PaymentSummary | None = None


# Contractor's own applications list


class MyApplicationJobSummary(BaseModel):
    id: int
    title: str
    category: str


class MyApplicationClientSummary(BaseModel):
    user_id: int
    full_name: str | None = None
    city: str | None = None
    country: str | None = None
    profile_picture: str | None = None


class MyApplicationSummary(BaseModel):
    id: int
    status: ApplicationStatus
    cover_letter: str
    created_at: datetime


class MyApplicationItemResponse(BaseModel):
    job: MyApplicationJobSummary
    client: MyApplicationClientSummary
    application: MyApplicationSummary


# Contractor's own application details

class MyApplicationDetailResponse(BaseModel):
    application: MyApplicationSummary
    job: JobResponse
    client: ClientPublicProfile
    reviews: TargetReviewsResponse
    negotiation: NegotiationSummaryResponse | None = None
    negotiation_updates: list[NegotiationEditResponse]
    contract: ContractSummary | None = None
    payment: PaymentSummary | None = None

class AcceptTermsResponse(BaseModel):
    message: str
    contract_id: int
    contract_status: str
