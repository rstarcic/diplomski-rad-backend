import logging
import os
from pathlib import Path
from typing import Literal

import aiohttp
from fastapi import status
from app.integrations.dashboard_schemas import (
    ContractDashboardSummary,
    PaymentDashboardSummary,
)
from app.integrations.schemas import (
    ContractCreateRequest,
    ContractServiceResponse,
    ContractSummary,
    PaymentProfileStatus,
    PaymentSummary,
)
from dotenv import load_dotenv
from errors import raise_core_error

logger = logging.getLogger(__name__)


load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

CONTRACT_SERVICE_URL = os.getenv(
    "CONTRACT_SERVICE_URL",
    "http://127.0.0.1:8002",
)
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://127.0.0.1:8003")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def _internal_headers() -> dict[str, str]:
    if not INTERNAL_SECRET:
        raise_core_error("contract_service_unavailable")

    return {"x-internal-secret": INTERNAL_SECRET}


async def create_contract(
    request: ContractCreateRequest,
) -> ContractServiceResponse:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{CONTRACT_SERVICE_URL}/internal/contracts",
                json=request.model_dump(mode="json"),
                headers=_internal_headers(),
            ) as response:
                if response.status >= status.HTTP_400_BAD_REQUEST:
                    error_body = await response.text()

                    print(
                        f"Contract service error "
                        f"status={response.status}, body={error_body}"
                    )

                    raise_core_error("contract_creation_failed")

                response_data = await response.json()

    except TimeoutError:
        raise_core_error("contract_service_timeout")

    except aiohttp.ClientError:
        raise_core_error("contract_service_unavailable")

    return ContractServiceResponse.model_validate(response_data)


async def update_contract_status_for_job(job_id: int, action: str) -> dict[str, object]:
    timeout = aiohttp.ClientTimeout(total=10)
    url = f"{CONTRACT_SERVICE_URL}/internal/contracts/job/{job_id}/{action}"

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.patch(
                url,
                headers=_internal_headers(),
            ) as response:
                if response.status >= status.HTTP_400_BAD_REQUEST:
                    error_body = await response.text()
                    print(
                        "Contract status update failed "
                        f"url={url}, status={response.status}, body={error_body}"
                    )
                    raise_core_error("contract_status_update_failed")
                print(f"Contract status updated url={url}, status={response.status}")
                return await response.json()
    except TimeoutError:
        print(f"Contract status update timed out url={url}")
        raise_core_error("contract_service_timeout")
    except aiohttp.ClientError as exc:
        print(f"Contract status update unavailable url={url}, error={exc}")
        raise_core_error("contract_service_unavailable")


async def create_pending_payment(contract_id: int) -> dict[str, object]:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{PAYMENT_SERVICE_URL}/internal/payments/pending",
                json={"contract_id": contract_id},
                headers=_internal_headers(),
            ) as response:
                if response.status >= status.HTTP_400_BAD_REQUEST:
                    raise_core_error("payment_creation_failed")

                return await response.json()
    except TimeoutError:
        raise_core_error("payment_service_timeout")
    except aiohttp.ClientError:
        raise_core_error("payment_service_unavailable")


async def get_payment_profile_status(
    user_id: int,
) -> PaymentProfileStatus | None:
    timeout = aiohttp.ClientTimeout(total=5)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{PAYMENT_SERVICE_URL}/internal/payments/profiles/{user_id}/status",
                headers=_internal_headers(),
            ) as response:
                if response.status == status.HTTP_404_NOT_FOUND:
                    return None

                if response.status >= status.HTTP_400_BAD_REQUEST:
                    raise_core_error("payment_service_unavailable")

                return PaymentProfileStatus.model_validate(await response.json())
    except TimeoutError:
        raise_core_error("payment_service_timeout")
    except aiohttp.ClientError:
        raise_core_error("payment_service_unavailable")


async def get_contract_summary(
    application_id: int,
) -> ContractSummary | None:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{CONTRACT_SERVICE_URL}/internal/contracts/application/{application_id}",
                headers=_internal_headers(),
            ) as response:
                if response.status == status.HTTP_404_NOT_FOUND:
                    return None

                if response.status >= status.HTTP_400_BAD_REQUEST:
                    raise_core_error("contract_summary_fetch_failed")

                return ContractSummary.model_validate(await response.json())
    except TimeoutError:
        raise_core_error("contract_service_timeout")
    except aiohttp.ClientError:
        raise_core_error("contract_service_unavailable")


async def get_payment_summary(
    application_id: int,
) -> PaymentSummary | None:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{PAYMENT_SERVICE_URL}/internal/payments/application/{application_id}",
                headers=_internal_headers(),
            ) as response:
                if response.status == status.HTTP_404_NOT_FOUND:
                    return None

                if response.status >= status.HTTP_400_BAD_REQUEST:
                    raise_core_error("payment_summary_fetch_failed")

                return PaymentSummary.model_validate(await response.json())

    except TimeoutError:
        raise_core_error("payment_service_timeout")
    except aiohttp.ClientError:
        raise_core_error("payment_service_unavailable")


async def get_contract_dashboard_summary(
    user_id: int,
    role: Literal["client", "contractor"],
) -> ContractDashboardSummary:
    return await _get_internal_dashboard_summary(
        url=f"{CONTRACT_SERVICE_URL}/internal/contracts/dashboard/{user_id}",
        role=role,
        response_model=ContractDashboardSummary,
        service_name="contract",
    )


async def get_payment_dashboard_summary(
    user_id: int,
    role: Literal["client", "contractor"],
) -> PaymentDashboardSummary:
    return await _get_internal_dashboard_summary(
        url=f"{PAYMENT_SERVICE_URL}/internal/payments/dashboard/{user_id}",
        role=role,
        response_model=PaymentDashboardSummary,
        service_name="payment",
    )


async def _get_internal_dashboard_summary(
    *,
    url: str,
    role: Literal["client", "contractor"],
    response_model,
    service_name: Literal["contract", "payment"],
):
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url,
                params={"role": role},
                headers=_internal_headers(),
            ) as response:
                if response.status >= status.HTTP_400_BAD_REQUEST:
                    raise_core_error(f"{service_name}_service_unavailable")
                return response_model.model_validate(await response.json())
    except TimeoutError:
        raise_core_error(f"{service_name}_service_timeout")
    except aiohttp.ClientError:
        raise_core_error(f"{service_name}_service_unavailable")
