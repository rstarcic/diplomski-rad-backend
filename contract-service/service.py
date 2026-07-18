import base64
import binascii
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader, select_autoescape
from models import Contract
from schemas import ContractCreateRequest, ContractJob, ContractParty, ContractTerms
from sqlalchemy import select
from sqlalchemy.orm import Session

TEMPLATES_DIR = Path(__file__).resolve().parent
template_environment = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(("html", "xml")),
)

SIGNATURE_DEADLINE = timedelta(days=1)


def _generate_contract_number() -> str:
    year = datetime.now(timezone.utc).year
    suffix = uuid4().hex[:8].upper()

    return f"CTR-{year}-{suffix}"


def _party_snapshot(prefix: str, party: ContractParty) -> dict:
    return {
        f"{prefix}_id": party.user_id,
        f"{prefix}_name": party.full_name,
        f"{prefix}_email": party.email,
        f"{prefix}_phone": party.phone,
        f"{prefix}_country": party.country,
        f"{prefix}_city": party.city,
    }


def _job_snapshot(job: ContractJob) -> dict:
    return {
        "job_id": job.id,
        "job_title": job.title,
        "job_description": job.description,
    }


def _contract_terms(terms: ContractTerms) -> dict:
    return {
        "budget_amount": terms.budget_amount,
        "budget_type": terms.budget_type,
        "currency": terms.currency,
        "duration": terms.duration,
        "hours_per_week": terms.hours_per_week,
        "deliverables": terms.deliverables,
    }


def _validate_signature_data_url(value: str) -> str:
    prefix = "data:image/png;base64,"

    if not value.startswith(prefix):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "signature_image_invalid",
                "message": "Signature must be a Base64-encoded PNG image.",
                "field": "signature",
            },
        )

    encoded = value[len(prefix) :]

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "signature_image_invalid",
                "message": "The signature image is not valid Base64 data.",
                "field": "signature",
            },
        )

    if len(image_bytes) > 500_000:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "signature_image_too_large",
                "message": "Signature image must not exceed 500 KB.",
                "field": "signature",
            },
        )

    return value


def create_contract(
    db: Session,
    request: ContractCreateRequest,
) -> Contract:
    existing_contract = db.scalar(
        select(Contract).where(Contract.application_id == request.application_id)
    )

    # Idempotentnost: ponovljeni zahtjev vraća isti ugovor.
    if existing_contract is not None:
        return existing_contract

    contract = Contract(
        contract_number=_generate_contract_number(),
        platform_name="WorkLink",
        application_id=request.application_id,
        negotiation_id=request.negotiation_id,
        status="pending_signatures",
        **_party_snapshot("client", request.client),
        **_party_snapshot("contractor", request.contractor),
        **_job_snapshot(request.job),
        **_contract_terms(request.terms),
    )

    db.add(contract)

    try:
        db.commit()
        db.refresh(contract)

    except Exception:
        db.rollback()
        raise

    return contract


def get_contract_by_id(
    db: Session,
    contract_id: int,
) -> Contract:
    contract = db.get(Contract, contract_id)

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="Contract not found",
        )

    _cancel_if_signature_deadline_passed(db, contract)

    return contract


def get_contract_by_application_id(
    db: Session,
    application_id: int,
) -> Contract:
    contract = db.scalar(
        select(Contract).where(Contract.application_id == application_id)
    )

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="Contract not found",
        )

    _cancel_if_signature_deadline_passed(db, contract)

    return contract


def update_contract_status_by_job(
    db: Session,
    job_id: int,
    action: str,
) -> Contract:
    contract = db.scalar(
        select(Contract).where(Contract.job_id == job_id).with_for_update()
    )

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="Contract not found.",
        )

    if action == "complete":
        target_status = "completed"

        if contract.status == "completed":
            return contract

        if contract.status != "active":
            raise HTTPException(
                status_code=409,
                detail="Only an active contract can be completed.",
            )

    elif action == "cancel":
        target_status = "cancelled"

        if contract.status == "cancelled":
            return contract

        if contract.status == "completed":
            raise HTTPException(
                status_code=409,
                detail="A completed contract cannot be cancelled.",
            )

    else:
        raise HTTPException(
            status_code=422,
            detail="Invalid contract action.",
        )

    contract.status = target_status

    try:
        db.commit()
        db.refresh(contract)
    except Exception:
        db.rollback()
        raise

    return contract


def authorize_contract_party(contract: Contract, user_id: int) -> None:
    if user_id not in {contract.client_id, contract.contractor_id}:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "contract_access_forbidden",
                "message": "Only a party to the contract may access it.",
                "field": None,
            },
        )


def _cancel_if_signature_deadline_passed(
    db: Session,
    contract: Contract,
) -> None:
    awaiting_signatures = contract.status in {
        "pending_signatures",
        "pending_client_signature",
        "pending_contractor_signature",
    }
    deadline = contract.created_at + SIGNATURE_DEADLINE

    if awaiting_signatures and datetime.now(timezone.utc) >= deadline:
        contract.status = "cancelled"

        try:
            db.commit()
            db.refresh(contract)
        except Exception:
            db.rollback()
            raise


def sign_contract(
    db: Session,
    contract_id: int,
    user_id: int,
    signature_data_url: str,
) -> Contract:
    contract = get_contract_by_id(db, contract_id)

    if contract.status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "contract_signature_deadline_expired",
                "message": "The contract was not signed by both parties within 24 hours.",
                "field": "status",
            },
        )

    signature = _validate_signature_data_url(signature_data_url)
    signed_at = datetime.now(timezone.utc)

    authorize_contract_party(contract, user_id)

    if user_id == contract.client_id:
        contract.client_signature_url = signature
        contract.client_signed_at = signed_at
    elif user_id == contract.contractor_id:
        contract.contractor_signature_url = signature
        contract.contractor_signed_at = signed_at
    if contract.client_signed_at and contract.contractor_signed_at:
        contract.status = "active"
        contract.starts_at = contract.starts_at or signed_at + timedelta(days=1)
        contract.ends_at = contract.ends_at or contract.starts_at + timedelta(
            days=contract.duration
        )
    elif contract.client_signed_at:
        contract.status = "pending_contractor_signature"
    else:
        contract.status = "pending_client_signature"

    try:
        db.commit()
        db.refresh(contract)
    except Exception:
        db.rollback()
        raise

    return contract


def render_contract_html(contract: Contract) -> str:
    template = template_environment.get_template("contract.html")

    return template.render(contract=contract)


def render_contract_pdf(contract: Contract) -> bytes:
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "pdf_renderer_unavailable",
                "message": "PDF generation is temporarily unavailable.",
                "field": None,
            },
        ) from exc

    html = render_contract_html(contract)

    return HTML(
        string=html,
        base_url=str(TEMPLATES_DIR),
    ).write_pdf()
