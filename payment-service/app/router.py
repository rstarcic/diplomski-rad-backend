import os

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import raise_not_found
from app.payments.schemas import PaymentProfileCreate, PaymentStatusResponse
from app.payments.service import create_payment_profile_if_not_exists, get_payment_status

router = APIRouter()

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _verify_internal(x_internal_secret: str = Header(...)):
    if INTERNAL_SECRET and x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/init", response_model=PaymentStatusResponse, status_code=201)
def init_payment_profile(
    data: PaymentProfileCreate,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_internal),
):
    return create_payment_profile_if_not_exists(db, data)


@router.get("/status/{user_id}", response_model=PaymentStatusResponse)
def get_status(user_id: int, db: Session = Depends(get_db)):
    profile = get_payment_status(db, user_id)
    if not profile:
        raise_not_found(f"Payment profile for user {user_id} not found")
    return profile
