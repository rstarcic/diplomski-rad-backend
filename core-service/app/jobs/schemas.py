from datetime import date, datetime
from typing import Literal

from app.profiles.schemas import ClientPublicProfile
from app.reviews.schemas import TargetReviewsResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LocationType = Literal["on_site", "hybrid", "remote"]
BudgetType = Literal["fixed", "hourly"]
JobStatus = Literal[
    "open",
    "awaiting_contract",
    "in_progress",
    "done_by_contractor",
    "completed_by_client",
    "incomplete",
    "cancelled",
]

TEXT_FIELDS = (
    "title",
    "category",
    "description",
    "location",
    "deliverables",
)


def normalize_location_type(value: object) -> object:
    if not isinstance(value, str):
        return value

    normalized = value.strip().lower().replace("-", "_")
    if normalized in ("onsite", "on_site"):
        return "on_site"

    return normalized


def strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return value

    stripped = value.strip()
    return stripped or None


def validate_future_deadline(value: datetime) -> datetime:
    if value.date() <= date.today():
        raise ValueError("Deadline must be after today.")

    return value


def clean_requirements(value: list[str]) -> list[str]:
    requirements = []
    seen = set()

    for requirement in value:
        stripped = requirement.strip()
        if not stripped:
            continue

        key = stripped.casefold()
        if key not in seen:
            requirements.append(stripped)
            seen.add(key)

    if not requirements:
        raise ValueError("At least one requirement is required.")

    return requirements


# Job create and update requests


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)

    location_type: LocationType
    location: str | None = Field(default=None, max_length=255)
    deadline: datetime

    deliverables: str = Field(..., min_length=1)
    requirements: list[str] = Field(..., min_length=1)

    budget_type: BudgetType
    budget_amount: float = Field(..., gt=0)

    duration: int = Field(..., gt=0)
    hours_per_week: int = Field(..., gt=0, le=168)

    @field_validator("location_type", mode="before")
    @classmethod
    def validate_location_type(cls, value: object) -> object:
        return normalize_location_type(value)

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return strip_optional_text(value)

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, value: datetime) -> datetime:
        return validate_future_deadline(value)

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, value: list[str]) -> list[str]:
        return clean_requirements(value)

    @model_validator(mode="after")
    def validate_location(self):
        if self.location_type in ("on_site", "hybrid") and not self.location:
            raise ValueError("Location is required for on-site or hybrid jobs.")

        if self.location_type == "remote":
            self.location = None

        return self


class JobCreate(JobBase):
    source_job_id: int | None = Field(default=None, gt=0)


class JobUpdate(JobBase):
    pass


# Full job responses

class JobResponse(BaseModel):
    id: int
    client_id: int
    source_job_id: int | None = None

    title: str
    category: str
    description: str

    location_type: LocationType
    location: str | None = None
    deadline: datetime

    deliverables: str
    requirements: list[str]

    budget_type: BudgetType
    budget_amount: float
    currency: Literal["EUR"] = "EUR"

    duration: int
    hours_per_week: int
    status: JobStatus

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Client posted jobs overview


class JobSummaryResponse(BaseModel):
    id: int
    replacement_job_id: int | None = None
    title: str
    category: str
    location_type: LocationType
    location: str | None = None
    budget_type: BudgetType
    status: JobStatus
    deadline: datetime
    updated_at: datetime
    applicants_count: int = 0
    new_applicants_count: int = 0
    contract_status: str = "not_started"
    payment_status: str = "no_payments"


# Contractor job search responses


class JobSearchItem(BaseModel):
    id: int
    title: str
    category: str
    description: str
    location_type: LocationType
    location: str | None = None
    budget_type: BudgetType
    budget_amount: float
    currency: Literal["EUR"] = "EUR"
    status: str
    deadline: datetime
    created_at: datetime


class JobSearchClient(BaseModel):
    user_id: int
    full_name: str | None = None
    profile_picture: str | None = None


class JobSearchItemResponse(BaseModel):
    job: JobSearchItem
    client: JobSearchClient


class JobFilterOptionsResponse(BaseModel):
    categories: list[str]
    cities: list[str]


# job details seen by contractor
class JobDetailsPageResponse(BaseModel):
    job: JobResponse
    client: ClientPublicProfile
    reviews: TargetReviewsResponse
    already_applied: bool
    application_status: Literal[
        "pending",
        "selected",
        "accepted",
        "rejected",
        "withdrawn",
    ] | None = None
