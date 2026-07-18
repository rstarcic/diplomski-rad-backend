import os
import secrets
import asyncio
from pathlib import Path

from database import get_db
from dependencies import get_current_user_id
from email_service import ContractEmailError, send_contract_email
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from integrations import notify_job_contract_activated
from schemas import (
    ContractCreateRequest,
    ContractEmailResponse,
    ContractResponse,
    ContractSignatureRequest,
)
from service import (
    authorize_contract_party,
    create_contract,
    get_contract_by_application_id,
    get_contract_by_id,
    render_contract_html,
    render_contract_pdf,
    sign_contract,
    update_contract_status_by_job,
)
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _verify_internal(x_internal_secret: str = Header(...)) -> None:
    if not INTERNAL_SECRET:
        raise HTTPException(503, detail="Internal API authentication is not configured.")
    if not secrets.compare_digest(x_internal_secret, INTERNAL_SECRET):
        raise HTTPException(403, detail="Forbidden")


internal_router = APIRouter(
    prefix="/internal/contracts",
    tags=["internal-contracts"],
    dependencies=[Depends(_verify_internal)],
)


@internal_router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract_endpoint(
    request: ContractCreateRequest,
    db: Session = Depends(get_db),
):
    return create_contract(db=db, request=request)


@internal_router.patch(
    "/job/{job_id}/complete",
    response_model=ContractResponse,
)
def complete_contract_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    return update_contract_status_by_job(
        db=db,
        job_id=job_id,
        action="complete",
    )


@internal_router.patch(
    "/job/{job_id}/cancel",
    response_model=ContractResponse,
)
def cancel_contract_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    return update_contract_status_by_job(
        db=db,
        job_id=job_id,
        action="cancel",
    )


router = APIRouter(prefix="/contracts", tags=["contracts"])


def _authorized_contract(contract_id: int, user_id: int, db: Session):
    contract = get_contract_by_id(db=db, contract_id=contract_id)
    authorize_contract_party(contract, user_id)
    return contract


@router.get("/application/{application_id}", response_model=ContractResponse)
def get_contract_by_application_endpoint(
    application_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    contract = get_contract_by_application_id(db=db, application_id=application_id)
    authorize_contract_party(contract, user_id)
    return contract


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract_endpoint(
    contract_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _authorized_contract(contract_id, user_id, db)


@router.post("/{contract_id}/sign", response_model=ContractResponse)
async def sign_contract_endpoint(
    contract_id: int,
    request: ContractSignatureRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    contract = sign_contract(
        db=db,
        contract_id=contract_id,
        user_id=user_id,
        signature_data_url=request.signature,
    )
    if contract.status == "active":
        await notify_job_contract_activated(contract.job_id)
    return contract


@router.get("/{contract_id}/preview", response_class=HTMLResponse)
def preview_contract_endpoint(
    contract_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    contract = _authorized_contract(contract_id, user_id, db)
    return HTMLResponse(content=render_contract_html(contract))


@router.get("/{contract_id}/download")
def download_contract_endpoint(
    contract_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    contract = _authorized_contract(contract_id, user_id, db)
    filename = f"{contract.contract_number}.pdf"
    return Response(
        content=render_contract_pdf(contract),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{contract_id}/email", response_model=ContractEmailResponse)
async def email_contract_endpoint(
    contract_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    contract = _authorized_contract(contract_id, user_id, db)
    if contract.status != "active":
        raise HTTPException(
            409,
            detail={
                "code": "contract_not_active",
                "message": "The contract must be signed by both parties before it can be emailed.",
                "field": "status",
            },
        )

    if user_id == contract.client_id:
        recipient_email = contract.client_email
        recipient_name = contract.client_name
    else:
        recipient_email = contract.contractor_email
        recipient_name = contract.contractor_name

    pdf_content = render_contract_pdf(contract)
    try:
        await asyncio.to_thread(
            send_contract_email,
            to_email=recipient_email,
            pdf_content=pdf_content,
            contract_number=contract.contract_number,
            job_title=contract.job_title,
            client_name=contract.client_name,
            contractor_name=contract.contractor_name,
            recipient_name=recipient_name,
            starts_at=(contract.starts_at.strftime("%d.%m.%Y.") if contract.starts_at else None),
            ends_at=(contract.ends_at.strftime("%d.%m.%Y.") if contract.ends_at else None),
        )
    except ContractEmailError:
        raise HTTPException(
            502,
            detail={
                "code": "contract_email_failed",
                "message": "The contract could not be sent. Please try again.",
                "field": None,
            },
        )

    return {"message": "The contract has been sent to your email."}
