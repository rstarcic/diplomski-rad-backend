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


class ContractPartySummary(BaseModel):
    user_id: int
    full_name: str
    email: str


class ContractPlatformSummary(BaseModel):
    name: str


class ContractResponse(BaseModel):
    id: int
    contract_number: str
    platform_name: str
    application_id: int
    negotiation_id: int | None

    client_id: int
    client_name: str
    client_email: str
    client: ContractPartySummary

    contractor_id: int
    contractor_name: str
    contractor_email: str
    contractor: ContractPartySummary

    platform: ContractPlatformSummary

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

    @classmethod
    def from_contract(cls, contract) -> "ContractResponse":
        return cls(
            id=contract.id,
            contract_number=contract.contract_number,
            platform_name=contract.platform_name,
            application_id=contract.application_id,
            negotiation_id=contract.negotiation_id,
            client_id=contract.client_id,
            client_name=contract.client_name,
            client_email=contract.client_email,
            client=ContractPartySummary(
                user_id=contract.client_id,
                full_name=contract.client_name,
                email=contract.client_email,
            ),
            contractor_id=contract.contractor_id,
            contractor_name=contract.contractor_name,
            contractor_email=contract.contractor_email,
            contractor=ContractPartySummary(
                user_id=contract.contractor_id,
                full_name=contract.contractor_name,
                email=contract.contractor_email,
            ),
            platform=ContractPlatformSummary(name=contract.platform_name),
            job_id=contract.job_id,
            job_title=contract.job_title,
            job_description=contract.job_description,
            budget_amount=contract.budget_amount,
            budget_type=contract.budget_type,
            currency=contract.currency,
            duration=contract.duration,
            hours_per_week=contract.hours_per_week,
            deliverables=contract.deliverables,
            status=contract.status,
            client_signed_at=contract.client_signed_at,
            client_signature_url=contract.client_signature_url,
            contractor_signed_at=contract.contractor_signed_at,
            contractor_signature_url=contract.contractor_signature_url,
            starts_at=contract.starts_at,
            ends_at=contract.ends_at,
            created_at=contract.created_at,
            updated_at=contract.updated_at,
        )
