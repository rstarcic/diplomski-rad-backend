from pydantic import BaseModel, Field


class PendingPaymentCreate(BaseModel):
    contract_id: int = Field(gt=0)


class InternalPaymentProfileStatusResponse(BaseModel):
    user_id: int
    role: str
    payment_setup_completed: bool
    payout_setup_completed: bool

    model_config = {"from_attributes": True}
