from pydantic import BaseModel


class PaymentProfileCreate(BaseModel):
    user_id: int
    role: str


class PaymentStatusResponse(BaseModel):
    user_id: int
    role: str
    payment_setup_completed: bool
    payout_setup_completed: bool

    model_config = {"from_attributes": True}
