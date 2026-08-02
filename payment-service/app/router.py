import os

from app.dependencies import get_current_user_id
from app.payments.schemas import PaymentStatusResponse
from app.schemas import PaymentProfileCreate
from app.service import create_payment_profile_if_not_exists, get_payment_status
from database import get_db
from errors import raise_payment_error
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _verify_internal(
    x_internal_secret: str = Header(...),
) -> None:
    if INTERNAL_SECRET and x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )


@router.post(
    "/init",
    response_model=PaymentStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def init_payment_profile(
    data: PaymentProfileCreate,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_internal),
):
    return create_payment_profile_if_not_exists(db, data)


@router.get("/status", response_model=PaymentStatusResponse)
def get_my_payment_status(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = get_payment_status(db, current_user_id)

    if profile is None:
        raise_payment_error("payment_profile_not_found")

    return profile
