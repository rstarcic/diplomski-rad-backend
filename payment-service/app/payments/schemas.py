from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentSetupRequest(BaseModel):
    address: str = Field(
        min_length=1,
        max_length=200,
    )
    postal_code: str = Field(
        min_length=1,
        max_length=20,
    )
    country_code: str = Field(
        min_length=2,
        max_length=2,
    )

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.strip().upper()

class ConnectOnboardingRequest(PaymentSetupRequest):
    pass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class ClientPaymentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: Literal["client"]
    payment_setup_completed: bool
    stripe_payment_method_id: str | None = None
    card_brand: str | None = None
    card_last4: str | None = None
    card_exp_month: int | None = None
    card_exp_year: int | None = None
    billing_address: str | None = None
    billing_postal_code: str | None = None
    billing_country_code: str | None = None


class ContractorPaymentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: Literal["contractor"]
    payout_setup_completed: bool
    details_submitted: bool
    payouts_enabled: bool
    charges_enabled: bool


PaymentStatusResponse = Annotated[
    ClientPaymentStatusResponse | ContractorPaymentStatusResponse,
    Field(discriminator="role"),
]

class JobPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    job_id: int
    application_id: int
    status: str


class JobPaymentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    status: Literal["pending", "paid", "cancelled", "overdue"]
    amount_minor: int
    currency: str
    checkout_attempt: int
    created_at: datetime
    updated_at: datetime

class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class ConnectOnboardingResponse(BaseModel):
    onboarding_url: str


class CurrentUser(BaseModel):
    id: int
    email: str
    role: str
    full_name: str | None = None
