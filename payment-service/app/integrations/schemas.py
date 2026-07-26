from pydantic import BaseModel, EmailStr


class ContractorProfile(BaseModel):
    user_id: int
    email: EmailStr
    role: str
    full_name: str | None = None
    about: str | None = None
    phone: str | None = None
    address: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    city: str | None = None


class ContractPaymentDetails(BaseModel):
    contract_id: int
    application_id: int
    job_id: int
    client_id: int
    client_name: str
    client_email: EmailStr
    contractor_id: int
    job_title: str
    amount_minor: int
    currency: str
    status: str
