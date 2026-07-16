from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContractParty(BaseModel):
    user_id: int
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = None
    country: str | None = None
    city: str | None = None


class ContractJob(BaseModel):
    id: int
    title: str
    description: str


class ContractTerms(BaseModel):
    budget_amount: float = Field(gt=0)
    budget_type: str
    currency: str = "EUR"
    duration: int = Field(gt=0)
    hours_per_week: int = Field(gt=0, le=168)
    deliverables: str


class ContractCreateRequest(BaseModel):
    application_id: int
    negotiation_id: int | None = None

    client: ContractParty
    contractor: ContractParty
    job: ContractJob
    terms: ContractTerms


class ContractSignatureRequest(BaseModel):
    signature: str = Field(min_length=1)


class ContractEmailResponse(BaseModel):
    message: str


class ContractResponse(BaseModel):
    id: int
    contract_number: str
    platform_name: str
    application_id: int
    negotiation_id: int | None

    client_id: int
    client_name: str
    client_email: str

    contractor_id: int
    contractor_name: str
    contractor_email: str

    job_id: int
    job_title: str
    job_description: str

    budget_amount: float
    budget_type: str
    currency: str
    duration: int
    hours_per_week: int
    deliverables: str

    status: str

    client_signed_at: datetime | None
    client_signature_url: str | None
    contractor_signed_at: datetime | None
    contractor_signature_url: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
