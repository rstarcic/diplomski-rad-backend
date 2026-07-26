from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import verify_internal
from app.internal.schemas import PendingPaymentCreate
from app.internal.service import create_pending_payment
from app.models import JobPayment
from app.payments.schemas import JobPaymentResponse, JobPaymentSummaryResponse
from database import get_db


router = APIRouter(
    prefix="/internal/payments",
    tags=["internal-payments"],
    dependencies=[Depends(verify_internal)],
)


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
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment
