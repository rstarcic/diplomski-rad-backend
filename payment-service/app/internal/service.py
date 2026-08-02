from datetime import UTC, datetime
from typing import Literal

from app.integrations.contract_client import get_contract_payment_details
from app.internal.dashboard_schemas import PaymentDashboardItem, PaymentDashboardSummary
from app.models import JobPayment
from sqlalchemy import func, select
from sqlalchemy.orm import Session


async def create_pending_payment(db: Session, contract_id: int) -> JobPayment:
    existing = db.scalar(
        select(JobPayment).where(JobPayment.contract_id == contract_id)
    )
    if existing:
        return existing

    contract = await get_contract_payment_details(contract_id)
    payment = JobPayment(
        contract_id=contract.contract_id,
        application_id=contract.application_id,
        job_id=contract.job_id,
        client_id=contract.client_id,
        contractor_id=contract.contractor_id,
        job_title=contract.job_title,
        amount_minor=contract.amount_minor,
        currency=contract.currency.lower(),
        status="pending",
    )
    try:
        db.add(payment)
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise
    return payment


def get_payment_dashboard_summary(
    db: Session,
    user_id: int,
    role: Literal["client", "contractor"],
) -> PaymentDashboardSummary:
    owner_filter = (
        JobPayment.client_id == user_id
        if role == "client"
        else JobPayment.contractor_id == user_id
    )
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pending_statuses = ("pending", "overdue")

    totals = db.execute(
        select(
            func.coalesce(
                func.sum(JobPayment.amount_minor).filter(JobPayment.status == "paid"),
                0,
            ),
            func.coalesce(
                func.sum(JobPayment.amount_minor).filter(
                    JobPayment.status == "paid",
                    JobPayment.updated_at >= month_start,
                ),
                0,
            ),
            func.coalesce(
                func.sum(JobPayment.amount_minor).filter(
                    JobPayment.status.in_(pending_statuses)
                ),
                0,
            ),
            func.count(JobPayment.id).filter(JobPayment.status.in_(pending_statuses)),
        ).where(owner_filter)
    ).one()

    recent = db.scalars(
        select(JobPayment)
        .where(owner_filter)
        .order_by(JobPayment.updated_at.desc())
        .limit(5)
    ).all()

    currency = recent[0].currency.upper() if recent else "EUR"
    return PaymentDashboardSummary(
        paid_total_minor=totals[0],
        paid_this_month_minor=totals[1],
        pending_total_minor=totals[2],
        pending_count=totals[3],
        currency=currency,
        recent=[
            PaymentDashboardItem(
                id=item.id,
                job_id=item.job_id,
                application_id=item.application_id,
                contract_id=item.contract_id,
                job_title=item.job_title,
                amount_minor=item.amount_minor,
                currency=item.currency,
                status=item.status,
                updated_at=item.updated_at,
            )
            for item in recent
        ],
    )
