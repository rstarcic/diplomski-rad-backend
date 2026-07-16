from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

NegotiationStatus = Literal[
    "pending_client",
    "pending_contractor",
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
    budget_amount: float
    currency: Literal["EUR"] = "EUR"
    hours_per_week: int
    duration: int
    deliverables: str
    message: str | None = None
    model_config = ConfigDict(from_attributes=True)
