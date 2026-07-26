from sqlalchemy.orm import Session

from app.integrations.contract_client import get_contract_payment_details
from app.models import JobPayment


async def create_pending_payment(db: Session, contract_id: int) -> JobPayment:
    existing = db.query(JobPayment).filter(JobPayment.contract_id == contract_id).first()
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
