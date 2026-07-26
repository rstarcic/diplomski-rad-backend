from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.contracts.service import get_contract_by_id
from app.internal.schemas import ContractPaymentDetailsResponse


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

    