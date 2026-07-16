from pydantic import BaseModel, Field


class ContractParty(BaseModel):
    user_id: int
    full_name: str
    email: str
    phone: str | None = None
    country: str | None = None
    city: str | None = None


class ContractJob(BaseModel):
    id: int
    title: str
    description: str


class ContractTermsRequest(BaseModel):
    budget_amount: float
    budget_type: str
    currency: str = "EUR"
    duration: int
    hours_per_week: int
    deliverables: str


class ContractCreateRequest(BaseModel):
    application_id: int
    negotiation_id: int | None = None

    client: ContractParty
    contractor: ContractParty
    job: ContractJob
    terms: ContractTermsRequest


class ContractServiceResponse(BaseModel):
    id: int
    contract_number: str
    application_id: int
    status: str


class ContractSignatureRequest(BaseModel):
    signature: str = Field(min_length=1)


class ContractServiceSignatureRequest(BaseModel):
    user_id: int
    signature: str
