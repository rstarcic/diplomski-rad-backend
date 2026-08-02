from typing import Literal

from pydantic import BaseModel

DashboardItemType = Literal[
    "application_received",
    "application_updated",
    "application_approved",
    "review_applications",
    "applications_in_progress",
    "contract_signature_required",
    "payment_updated",
    "payment_released",
    "setup_payment",
    "setup_payout",
]


class DashboardStatCard(BaseModel):
    id: str
    title: str
    value: int | str
    subtitle: str


class DashboardListItem(BaseModel):
    id: str
    type: DashboardItemType
    title: str
    subtitle: str
    meta: str
    metaAccent: Literal["warning", "info", "success"] | None = None
    job_id: int | None = None
    application_id: int | None = None
    contract_id: int | None = None
    payment_id: int | None = None


class DashboardPaymentSummary(BaseModel):
    availableBalance: str
    pendingPayments: str
    nextPayoutDate: str
    status: str


class DashboardResponse(BaseModel):
    stats_cards: list[DashboardStatCard]
    recent_activity: list[DashboardListItem]
    pending_actions: list[DashboardListItem]
    payment_summary: DashboardPaymentSummary
