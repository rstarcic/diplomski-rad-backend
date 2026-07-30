import asyncio

from app.contracts.schemas import (
    ContractEmailResponse,
    ContractResponse,
    ContractSignatureRequest,
)
from app.contracts.service import (
    authorize_contract_party,
    get_contract_by_application_id,
    get_contract_by_id,
    render_contract_html,
    render_contract_pdf,
    sign_contract,
)
from app.documents.email_service import ContractEmailError, send_contract_email
from app.integrations.core_client import notify_job_contract_activated
from database import get_db
from dependencies import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

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
    return ContractResponse.model_validate(contract)


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
    if contract.status not in {"active", "completed"}:
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

    try:
        pdf_content = render_contract_pdf(contract)
    except Exception:
        return {
            "message": "The contract is ready, but PDF generation is currently unavailable."
        }

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
            starts_at=(
                contract.starts_at.strftime("%d.%m.%Y.") if contract.starts_at else None
            ),
            ends_at=(
                contract.ends_at.strftime("%d.%m.%Y.") if contract.ends_at else None
            ),
        )
    except ContractEmailError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "email_delivery_failed",
                "message": str(exc),
            },
        ) from exc

    return {"message": "The contract has been sent to your email."}
