from typing import Literal

from app.contracts.schemas import ContractCreateRequest, ContractResponse
from app.contracts.service import (
    create_contract,
    get_contract_by_application_id,
    update_contract_status_by_job,
)
from app.internal.dashboard_schemas import ContractDashboardSummary
from app.internal.schemas import ContractPaymentDetailsResponse
from app.internal.service import (
    get_contract_dashboard_summary,
    get_contract_payment_details,
)
from database import get_db
from dependencies import verify_internal
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/internal/contracts",
    tags=["internal-contracts"],
    dependencies=[Depends(verify_internal)],
)


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract_endpoint(
    request: ContractCreateRequest,
    db: Session = Depends(get_db),
):
    contract = create_contract(db=db, request=request)
    return ContractResponse.model_validate(contract)


@router.patch("/job/{job_id}/complete", response_model=ContractResponse)
def complete_contract_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    contract = update_contract_status_by_job(
        db=db,
        job_id=job_id,
        action="complete",
    )
    return ContractResponse.model_validate(contract)


@router.patch("/job/{job_id}/cancel", response_model=ContractResponse)
def cancel_contract_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    contract = update_contract_status_by_job(
        db=db,
        job_id=job_id,
        action="cancel",
    )
    return ContractResponse.model_validate(contract)


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
    return ContractResponse.model_validate(contract)


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
