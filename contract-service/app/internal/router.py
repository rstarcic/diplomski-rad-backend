from typing import Literal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.contracts.schemas import ContractCreateRequest, ContractResponse
from app.contracts.service import create_contract, update_contract_status_by_job, get_contract_by_application_id
from app.internal.schemas import ContractPaymentDetailsResponse
from app.internal.service import (
    get_contract_dashboard_summary,
    get_contract_payment_details,
)
from database import get_db
from dependencies import _verify_internal
from app.internal.dashboard_schemas import ContractDashboardSummary


router = APIRouter(
    prefix="/internal/contracts",
    tags=["internal-contracts"],
    dependencies=[Depends(_verify_internal)],
)


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract_endpoint(
    request: ContractCreateRequest,
    db: Session = Depends(get_db),
):
    return ContractResponse.from_contract(create_contract(db=db, request=request))


@router.patch("/job/{job_id}/complete", response_model=ContractResponse)
def complete_contract_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    return ContractResponse.from_contract(
        update_contract_status_by_job(db=db, job_id=job_id, action="complete")
    )


@router.patch("/job/{job_id}/cancel", response_model=ContractResponse)
def cancel_contract_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    return ContractResponse.from_contract(
        update_contract_status_by_job(db=db, job_id=job_id, action="cancel")
    )


@router.get(
    "/{contract_id}/payment-details",
    response_model=ContractPaymentDetailsResponse,
)
def get_contract_payment_details_endpoint(
    contract_id: int,
    db: Session = Depends(get_db),
):
    return get_contract_payment_details(db=db, contract_id=contract_id)


@router.get(
    "/application/{application_id}",
    response_model=ContractResponse,
)
def get_contract_by_application_endpoint(
    application_id: int,
    db: Session = Depends(get_db),
):
    contract = get_contract_by_application_id(
        db=db,
        application_id=application_id,
    )
    return ContractResponse.from_contract(contract)


@router.get(
    "/dashboard/{user_id}",
    response_model=ContractDashboardSummary,
)
def get_contract_dashboard_summary_endpoint(
    user_id: int,
    role: Literal["client", "contractor"],
    db: Session = Depends(get_db),
):
    return get_contract_dashboard_summary(
        db=db,
        user_id=user_id,
        role=role,
    )
