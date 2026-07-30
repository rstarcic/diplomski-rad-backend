from typing import Literal

from pydantic import BaseModel


class DashboardStatCard(BaseModel):
    id: str
    title: str
    value: int | str
    subtitle: str


class DashboardListItem(BaseModel):
    id: str
    title: str
    subtitle: str
    meta: str
    metaAccent: Literal["warning", "info", "success"] | None = None


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
