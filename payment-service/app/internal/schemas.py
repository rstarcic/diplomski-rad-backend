from pydantic import BaseModel, Field


class PendingPaymentCreate(BaseModel):
    contract_id: int = Field(gt=0)
