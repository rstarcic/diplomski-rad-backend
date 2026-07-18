from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

NegotiationStatus = Literal[
    "pending_client",
    "pending_contractor",
    "accepted",
    "rejected",
    "expired",
]

NegotiationSubmittedBy = Literal["client", "contractor"]


class NegotiationSummaryResponse(BaseModel):
    id: int
    status: NegotiationStatus

    model_config = ConfigDict(from_attributes=True)


class NegotiationEditResponse(BaseModel):
    id: int
    round_number: int
    submitted_by: NegotiationSubmittedBy
    submitted_at: datetime
    budget_type: Literal["fixed", "hourly"]
    budget_amount: float
    currency: Literal["EUR"] = "EUR"
    hours_per_week: int
    duration: int
    deliverables: str
    message: str | None = None
    model_config = ConfigDict(from_attributes=True)


class CounterOfferRequest(BaseModel):
    budget_amount: float = Field(..., gt=0)
    budget_type: Literal["fixed", "hourly"]
    hours_per_week: int = Field(..., gt=0, le=168)
    duration: int = Field(..., gt=0)
    deliverables: str = Field(..., min_length=1)
    message: str | None = Field(default=None, max_length=5000)

    @field_validator("deliverables", "message", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None


class CounterOfferResponse(BaseModel):
    negotiation_id: int
    negotiation_status: NegotiationStatus
    update: NegotiationEditResponse
