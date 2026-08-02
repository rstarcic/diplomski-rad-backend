from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

ContractStatus = Literal[
    "pending_signatures",
    "pending_client_signature",
    "pending_contractor_signature",
    "active",
    "completed",
    "cancelled",
]
BudgetType = Literal["fixed", "hourly"]
PaymentStatus = Literal["pending", "paid", "cancelled", "overdue"]


class PaymentProfileStatus(BaseModel):
    user_id: int
    role: Literal["client", "contractor"]
    payment_setup_completed: bool
    payout_setup_completed: bool


class ContractParty(BaseModel):
    """A snapshot of a user who becomes one of the contracting parties."""

    user_id: int = Field(gt=0)
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = None
    country: str | None = None
    city: str | None = None


class ContractJob(BaseModel):
    """A snapshot of the job stored in the contract."""

    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class ContractTermsRequest(BaseModel):
    """The agreed financial terms and timeframe of the contract."""

    budget_amount: Decimal = Field(gt=0)
    budget_type: BudgetType
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    duration: int = Field(
        gt=0,
        description="Contract duration in days.",
    )
    hours_per_week: int = Field(gt=0, le=168)
    deliverables: str = Field(min_length=1)


class ContractCreateRequest(BaseModel):
    """The payload sent by the core service to create a contract."""

    application_id: int = Field(gt=0)
    negotiation_id: int | None = Field(default=None, gt=0)

    client: ContractParty
    contractor: ContractParty
    job: ContractJob
    terms: ContractTermsRequest


class ContractServiceResponse(BaseModel):
    """A minimal response returned after the contract is created."""

    id: int
    contract_number: str
    application_id: int
    status: ContractStatus


class ContractPartySummary(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr


class ContractPlatformSummary(BaseModel):
    name: str


class ContractSummary(BaseModel):
    """A contract summary displayed in the application details."""

    id: int
    contract_number: str
    status: ContractStatus

    platform_name: str | None = None
    client_name: str | None = None
    contractor_name: str | None = None
    client: ContractPartySummary | None = None
    contractor: ContractPartySummary | None = None
    platform: ContractPlatformSummary | None = None

    budget_amount: float
    budget_type: BudgetType
    currency: str = Field(
        default="EUR",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
    )
    duration: int
    hours_per_week: int
    deliverables: str

    client_signed_at: datetime | None
    contractor_signed_at: datetime | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime


class PaymentSummary(BaseModel):
    id: int = Field(gt=0)
    contract_id: int = Field(gt=0)
    status: PaymentStatus
    amount_minor: int = Field(ge=0)
    currency: str = Field(
        min_length=3,
        max_length=3,
    )
    checkout_attempt: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
