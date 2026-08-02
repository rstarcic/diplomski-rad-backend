from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.contracts.service import get_contract_by_id
from app.internal.dashboard_schemas import (
    ContractDashboardItem,
    ContractDashboardSummary,
)
from app.internal.schemas import ContractPaymentDetailsResponse
from fastapi import HTTPException, status
from models import Contract
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def _to_minor_units(amount: float | Decimal) -> int:
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
        amount_minor=_to_minor_units(contract.budget_amount),
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
    now = datetime.now(UTC)
    ending_soon = now + timedelta(days=7)
    pending_statuses = (
        ("pending_signatures", "pending_client_signature")
        if role == "client"
        else ("pending_signatures", "pending_contractor_signature")
    )

    counts = db.execute(
        select(
            func.count(Contract.id)
            .filter(Contract.status == "active")
            .label("active_count"),
            func.count(Contract.id)
            .filter(Contract.status.in_(("active", "completed")))
            .label("signed_count"),
            func.count(Contract.id)
            .filter(
                Contract.status == "active",
                Contract.ends_at.is_not(None),
                Contract.ends_at >= now,
                Contract.ends_at <= ending_soon,
            )
            .label("ending_soon_count"),
            func.count(Contract.id)
            .filter(Contract.status.in_(pending_statuses))
            .label("pending_signature_count"),
        ).where(owner_filter)
    ).one()

    recent = db.scalars(
        select(Contract)
        .where(owner_filter)
        .order_by(Contract.updated_at.desc())
        .limit(5)
    ).all()

    pending_signatures = db.scalars(
        select(Contract)
        .where(
            owner_filter,
            Contract.status.in_(pending_statuses),
        )
        .order_by(Contract.updated_at.desc())
        .limit(5)
    ).all()

    def dashboard_item(contract: Contract) -> ContractDashboardItem:
        return ContractDashboardItem(
            id=contract.id,
            job_id=contract.job_id,
            application_id=contract.application_id,
            job_title=contract.job_title,
            status=contract.status,
            updated_at=contract.updated_at,
        )

    return ContractDashboardSummary(
        active_count=counts.active_count,
        signed_count=counts.signed_count,
        ending_soon_count=counts.ending_soon_count,
        pending_signature_count=counts.pending_signature_count,
        recent=[dashboard_item(item) for item in recent],
        pending_signatures=[dashboard_item(item) for item in pending_signatures],
    )
