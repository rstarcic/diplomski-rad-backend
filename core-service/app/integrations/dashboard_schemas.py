from datetime import datetime

from pydantic import BaseModel


class ContractDashboardItem(BaseModel):
    id: int
    job_title: str
    status: str
    updated_at: datetime


class ContractDashboardSummary(BaseModel):
    active_count: int
    signed_count: int
    ending_soon_count: int
    pending_signature_count: int
    recent: list[ContractDashboardItem]


class PaymentDashboardItem(BaseModel):
    id: int
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
