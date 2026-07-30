from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.contracts.service import get_contract_by_id
from app.internal.dashboard_schemas import (
    ContractDashboardItem,
    ContractDashboardSummary,
)
from app.internal.schemas import ContractPaymentDetailsResponse
from models import Contract


def to_minor_units(amount: float | Decimal) -> int:
    decimal_amount = Decimal(str(amount))

    return int(
        (decimal_amount * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def get_contract_payment_details(
    *,
    db: Session,
    contract_id: int,
) -> ContractPaymentDetailsResponse:
    contract = get_contract_by_id(
        db=db,
        contract_id=contract_id,
    )

    if contract.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "contract_not_payable",
                "message": (
                    "The contract must be completed before payment " "can be initiated."
                ),
                "field": "status",
            },
        )

    return ContractPaymentDetailsResponse(
        contract_id=contract.id,
        application_id=contract.application_id,
        job_id=contract.job_id,
        client_id=contract.client_id,
        client_name=contract.client_name,
        client_email=contract.client_email,
        contractor_id=contract.contractor_id,
        job_title=contract.job_title,
        amount_minor=to_minor_units(contract.budget_amount),
        currency=contract.currency.lower(),
        status=contract.status,
    )


def get_contract_dashboard_summary(
    db: Session,
    user_id: int,
    role: Literal["client", "contractor"],
) -> ContractDashboardSummary:
    owner_filter = (
        Contract.client_id == user_id
        if role == "client"
        else Contract.contractor_id == user_id
    )
    now = datetime.now(timezone.utc)
    ending_soon = now + timedelta(days=7)
    pending_statuses = (
        ("pending_signatures", "pending_client_signature")
        if role == "client"
        else ("pending_signatures", "pending_contractor_signature")
    )

    counts = db.execute(
        select(
            func.count(Contract.id).filter(Contract.status == "active"),
            func.count(Contract.id).filter(
                Contract.status.in_(("active", "completed"))
            ),
            func.count(Contract.id).filter(
                Contract.status == "active",
                Contract.ends_at.isnot(None),
                Contract.ends_at >= now,
                Contract.ends_at <= ending_soon,
            ),
            func.count(Contract.id).filter(
                Contract.status.in_(pending_statuses)
            ),
        ).where(owner_filter)
    ).one()

    recent = db.scalars(
        select(Contract)
        .where(owner_filter)
        .order_by(Contract.updated_at.desc())
        .limit(5)
    ).all()

    return ContractDashboardSummary(
        active_count=counts[0],
        signed_count=counts[1],
        ending_soon_count=counts[2],
        pending_signature_count=counts[3],
        recent=[
            ContractDashboardItem(
                id=item.id,
                job_title=item.job_title,
                status=item.status,
                updated_at=item.updated_at,
            )
            for item in recent
        ],
    )
