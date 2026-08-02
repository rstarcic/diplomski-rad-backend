from datetime import datetime

from pydantic import BaseModel


class PaymentDashboardItem(BaseModel):
    id: int
    job_id: int
    application_id: int
    contract_id: int
    job_title: str
    amount_minor: int
    currency: str
    status: str
    updated_at: datetime


class PaymentDashboardSummary(BaseModel):
    paid_total_minor: int
    paid_this_month_minor: int
    pending_total_minor: int
    pending_count: int
    currency: str
    recent: list[PaymentDashboardItem]
