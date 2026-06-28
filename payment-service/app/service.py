from sqlalchemy.orm import Session

from app.payments.models import PaymentProfile
from app.payments.schemas import PaymentProfileCreate


def create_payment_profile_if_not_exists(db: Session, data: PaymentProfileCreate) -> PaymentProfile:
    existing = db.query(PaymentProfile).filter(PaymentProfile.user_id == data.user_id).first()
    if existing:
        return existing

    profile = PaymentProfile(**data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_payment_status(db: Session, user_id: int) -> PaymentProfile | None:
    return db.query(PaymentProfile).filter(PaymentProfile.user_id == user_id).first()
