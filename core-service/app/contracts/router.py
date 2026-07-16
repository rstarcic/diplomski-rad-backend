from app.dependencies import get_current_user
from app.integrations.client import sign_contract
from app.integrations.schemas import (
    ContractServiceResponse,
    ContractServiceSignatureRequest,
    ContractSignatureRequest,
)
from app.profiles.models import Profile
from fastapi import APIRouter, Depends

router = APIRouter(tags=["contracts"])


@router.post(
    "/{contract_id}/sign",
    response_model=ContractServiceResponse,
)
async def sign_contract_endpoint(
    contract_id: int,
    request: ContractSignatureRequest,
    current_user: Profile = Depends(get_current_user),
):
    return await sign_contract(
        contract_id=contract_id,
        request=ContractServiceSignatureRequest(
            user_id=current_user.user_id,
            signature=request.signature,
        ),
    )
