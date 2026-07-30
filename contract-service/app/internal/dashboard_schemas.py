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
