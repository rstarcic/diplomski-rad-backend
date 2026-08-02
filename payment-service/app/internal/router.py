from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import verify_internal
from app.internal.schemas import (
    InternalPaymentProfileStatusResponse,
    PendingPaymentCreate,
)
from app.internal.service import (
    create_pending_payment,
    get_payment_dashboard_summary,
)
from app.models import JobPayment, PaymentProfile
from app.payments.schemas import (
    JobPaymentResponse,
    JobPaymentSummaryResponse,
)
from database import get_db
from app.internal.dashboard_schemas import PaymentDashboardSummary


router = APIRouter(
    prefix="/internal/payments",
    tags=["internal-payments"],
    dependencies=[Depends(verify_internal)],
)


@router.get(
    "/profiles/{user_id}/status",
    response_model=InternalPaymentProfileStatusResponse,
)
def get_payment_profile_status(
    user_id: int,
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(PaymentProfile).where(PaymentProfile.user_id == user_id)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment profile not found",
        )

    return profile


@router.post("/pending", response_model=JobPaymentResponse, status_code=status.HTTP_201_CREATED)
async def initialize_pending_payment(
    data: PendingPaymentCreate,
    db: Session = Depends(get_db),
):
    return await create_pending_payment(db, data.contract_id)


@router.get(
    "/application/{application_id}",
    response_model=JobPaymentSummaryResponse,
)
def get_payment_by_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    payment = db.scalar(
        select(JobPayment).where(JobPayment.application_id == application_id)
    )
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return payment


@router.get(
    "/dashboard/{user_id}",
    response_model=PaymentDashboardSummary,
)
def get_payment_dashboard_summary_endpoint(
    user_id: int,
    role: Literal["client", "contractor"],
    db: Session = Depends(get_db),
):
    return get_payment_dashboard_summary(
        db=db,
        user_id=user_id,
        role=role,
    )
