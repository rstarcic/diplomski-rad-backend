import os

import aiohttp
from fastapi import status

from app.dependencies import INTERNAL_SECRET
from app.integrations.schemas import ContractPaymentDetails
from errors import payment_error, raise_payment_error


CONTRACT_SERVICE_URL = os.getenv("CONTRACT_SERVICE_URL", "http://127.0.0.1:8002")


async def get_contract_payment_details(contract_id: int) -> ContractPaymentDetails:
    if not INTERNAL_SECRET:
        raise_payment_error("internal_authentication_unavailable")

    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{CONTRACT_SERVICE_URL}/internal/contracts/{contract_id}/payment-details",
                headers={"x-internal-secret": INTERNAL_SECRET},
            ) as response:
                if response.status == status.HTTP_404_NOT_FOUND:
                    raise_payment_error("contract_not_found")
                if response.status == status.HTTP_409_CONFLICT:
                    raise_payment_error("contract_not_payable")
                if response.status >= status.HTTP_400_BAD_REQUEST:
                    raise_payment_error("contract_service_failed")
                data = await response.json()
    except TimeoutError as exc:
        raise payment_error("contract_service_timeout") from exc
    except aiohttp.ClientError as exc:
        raise payment_error("contract_service_unavailable") from exc

    return ContractPaymentDetails.model_validate(data)
