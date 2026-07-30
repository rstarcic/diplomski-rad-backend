from app.applications.schemas import (
    AcceptTermsResponse,
    ApplicationCreate,
    ApplicationCreateResponse,
    ApplicationDecision,
    ApplicationDecisionResponse,
    JobApplicationDetailResponse,
    JobApplicationItemResponse,
    MyApplicationDetailResponse,
    MyApplicationItemResponse,
)
from app.applications.service import (
    create_job_application,
    decide_job_application,
    get_job_application_detail,
    get_job_applications,
    get_my_application_detail,
    get_my_applications,
    withdraw_job_application,
)
from app.dependencies import get_current_user
from app.integrations.client import get_payment_profile_status
from app.negotiations.service import (
    accept_application_terms,
    reject_application_terms,
    submit_application_counter_offer,
)
from app.negotiations.schemas import CounterOfferRequest, CounterOfferResponse
from app.profiles.models import Profile
from database import get_db
from errors import raise_core_error
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.patch(
    "/jobs/{job_id}/applications/{application_id}/withdraw",
    response_model=ApplicationDecisionResponse,
)
async def withdraw_job_application_endpoint(
    job_id: int,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    return await withdraw_job_application(
        db=db,
        job_id=job_id,
        application_id=application_id,
        contractor_id=current_user.user_id,
    )


@router.get("/applications/me", response_model=list[MyApplicationItemResponse])
def get_my_applications_endpoint(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    applications = get_my_applications(
        db=db,
        contractor_id=current_user.user_id,
    )

    if applications is None:
        raise_core_error("applications_not_found")

    return applications


@router.get(
    "/jobs/{job_id}/applications", response_model=list[JobApplicationItemResponse]
)
def get_job_applications_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    applications = get_job_applications(
        db=db,
        client_id=current_user.user_id,
        job_id=job_id,
    )

    if applications is None:
        raise_core_error("applications_not_found")

    return applications


@router.get(
    "/applications/{application_id}/me",
    response_model=MyApplicationDetailResponse,
)
async def get_my_application_detail_endpoint(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    application = await get_my_application_detail(
        db=db,
        contractor_id=current_user.user_id,
        application_id=application_id,
    )

    if application is None:
        raise_core_error("application_not_found")

    return application


@router.get(
    "/jobs/{job_id}/applications/{application_id}",
    response_model=JobApplicationDetailResponse,
)
async def get_job_application_detail_endpoint(
    job_id: int,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    application = await get_job_application_detail(
        db=db,
        client_id=current_user.user_id,
        job_id=job_id,
        application_id=application_id,
    )

    if application is None:
        raise_core_error("application_not_found")

    return application


@router.post(
    "/jobs/{job_id}/applications",
    response_model=ApplicationCreateResponse,
    status_code=201,
)
async def create_application_endpoint(
    job_id: int,
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "contractor":
        raise_core_error("forbidden")

    if not current_user.profile_completed:
        raise_core_error("profile_completion_required")

    payment_status = await get_payment_profile_status(current_user.user_id)
    if payment_status is None or not payment_status.payout_setup_completed:
        raise_core_error("payout_setup_required")

    return create_job_application(
        db=db,
        job_id=job_id,
        contractor_id=current_user.user_id,
        data=data,
    )

# Clinet can reject or accept contractor's application
@router.patch(
    "/jobs/{job_id}/applications/{application_id}/decision",
    response_model=ApplicationDecisionResponse,
)
def decide_job_application_endpoint(
    job_id: int,
    application_id: int,
    data: ApplicationDecision,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    if current_user.role != "client":
        raise_core_error("forbidden")

    return decide_job_application(
        db=db,
        client_id=current_user.user_id,
        job_id=job_id,
        application_id=application_id,
        decision=data.decision,
    )


# Accept terms
@router.post(
    "/jobs/{job_id}/applications/{application_id}/accept",
    response_model=AcceptTermsResponse,
)
async def accept_application_terms_endpoint(
    job_id: int,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    contract = await accept_application_terms(
        db=db,
        job_id=job_id,
        application_id=application_id,
        user_id=current_user.user_id,
    )
    return AcceptTermsResponse(
        message="Terms accepted and contract created successfully.",
        contract_id=contract.id,
        contract_status=contract.status,
    )

# Reject terms
@router.post(
    "/jobs/{job_id}/applications/{application_id}/reject",
    response_model=ApplicationDecisionResponse,
)
def reject_application_terms_endpoint(
    job_id: int,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    application = reject_application_terms(
        db=db,
        job_id=job_id,
        application_id=application_id,
        current_user=current_user,
    )

    return ApplicationDecisionResponse(
        id=application.id,
        status=application.status,
    )

# Counteroffer
@router.post(
    "/jobs/{job_id}/applications/{application_id}/counter-offer",
    response_model=CounterOfferResponse,
)
def submit_counter_offer_endpoint(
    job_id: int,
    application_id: int,
    data: CounterOfferRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return submit_application_counter_offer(
        db=db,
        job_id=job_id,
        application_id=application_id,
        current_user=current_user,
        data=data,
    )
