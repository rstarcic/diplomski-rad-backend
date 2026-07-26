from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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


class ContractParty(BaseModel):
    """Snapshot korisnika koji postaje jedna od ugovornih strana."""

    user_id: int = Field(gt=0)
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=1, max_length=255)
    phone: str | None = None
    country: str | None = None
    city: str | None = None


class ContractJob(BaseModel):
    """Snapshot posla koji se sprema u ugovor."""

    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class ContractTermsRequest(BaseModel):
    """Dogovoreni financijski i vremenski uvjeti ugovora."""

    budget_amount: float = Field(gt=0)
    budget_type: BudgetType
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    duration: int = Field(gt=0, description="Trajanje ugovora u danima.")
    hours_per_week: int = Field(gt=0, le=168)
    deliverables: str = Field(min_length=1)


class ContractCreateRequest(BaseModel):
    """Payload koji core-service šalje contract-serviceu pri izradi ugovora."""

    application_id: int = Field(gt=0)
    negotiation_id: int | None = Field(default=None, gt=0)

    client: ContractParty
    contractor: ContractParty
    job: ContractJob
    terms: ContractTermsRequest


class ContractServiceResponse(BaseModel):
    """Minimalni odgovor contract-servicea nakon izrade ugovora."""

    id: int
    contract_number: str
    application_id: int
    status: ContractStatus


class ContractPartySummary(BaseModel):
    user_id: int
    full_name: str
    email: str


class ContractPlatformSummary(BaseModel):
    name: str


class ContractSummary(BaseModel):
    """Sažetak ugovora prikazan u detaljima prijave."""

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
    currency: str
    duration: int
    hours_per_week: int
    deliverables: str

    client_signed_at: datetime | None
    contractor_signed_at: datetime | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime


class PaymentSummary(BaseModel):
    id: int
    contract_id: int
    status: Literal["pending", "paid", "cancelled", "overdue"]
    amount_minor: int
    currency: str
    checkout_attempt: int
    created_at: datetime
    updated_at: datetime