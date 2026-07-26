from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ContractPaymentDetailsResponse(BaseModel):
    contract_id: int = Field(gt=0)
    application_id: int = Field(gt=0)
    job_id: int = Field(gt=0)

    client_id: int = Field(gt=0)
    client_name: str = Field(min_length=1, max_length=200)
    client_email: EmailStr

    contractor_id: int = Field(gt=0)
    job_title: str = Field(min_length=1)

    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)

    status: Literal["completed"]
