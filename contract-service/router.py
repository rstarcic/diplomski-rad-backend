import os
import secrets
from pathlib import Path

from database import get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from schemas import ContractCreateRequest, ContractResponse, ContractSignatureRequest
from service import (
    create_contract,
    get_contract_by_application_id,
    get_contract_by_id,
    render_contract_html,
    sign_contract,
)
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)

INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _verify_internal(x_internal_secret: str = Header(...)) -> None:
    if not INTERNAL_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Internal API authentication is not configured.",
        )

    if not secrets.compare_digest(x_internal_secret, INTERNAL_SECRET):
        raise HTTPException(status_code=403, detail="Forbidden")


internal_router = APIRouter(
    prefix="/internal/contracts",
    tags=["internal-contracts"],
    dependencies=[Depends(_verify_internal)],
)


@internal_router.post(
    "",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contract_endpoint(
    request: ContractCreateRequest,
    db: Session = Depends(get_db),
):
    return create_contract(
        db=db,
        request=request,
    )


@internal_router.post(
    "/{contract_id}/sign",
    response_model=ContractResponse,
)
def sign_contract_internal_endpoint(
    contract_id: int,
    request: ContractSignatureRequest,
    db: Session = Depends(get_db),
):
    return sign_contract(
        db=db,
        contract_id=contract_id,
        request=request,
    )


router = APIRouter(
    prefix="/contracts",
    tags=["contracts"],
)


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
)
def get_contract_endpoint(
    contract_id: int,
    db: Session = Depends(get_db),
):
    return get_contract_by_id(
        db=db,
        contract_id=contract_id,
    )


@router.get(
    "/{contract_id}/preview",
    response_class=HTMLResponse,
)
def preview_contract_endpoint(
    contract_id: int,
    db: Session = Depends(get_db),
):
    contract = get_contract_by_id(
        db=db,
        contract_id=contract_id,
    )

    return HTMLResponse(content=render_contract_html(contract))


@router.get(
    "/application/{application_id}",
    response_model=ContractResponse,
)
def get_contract_by_application_endpoint(
    application_id: int,
    db: Session = Depends(get_db),
):
    return get_contract_by_application_id(
        db=db,
        application_id=application_id,
    )
