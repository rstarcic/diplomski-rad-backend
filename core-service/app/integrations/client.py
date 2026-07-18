import asyncio
import os
from pathlib import Path

import aiohttp
from app.integrations.schemas import (
    ContractCreateRequest,
    ContractServiceResponse,
)
from errors import raise_core_error
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=True)

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
                if response.status >= 400:
                    error_body = await response.text()

                    print(
                        f"Contract service error "
                        f"status={response.status}, body={error_body}"
                    )

                    raise_core_error("contract_creation_failed")

                response_data = await response.json()

    except asyncio.TimeoutError:
        raise_core_error("contract_service_timeout")

    except aiohttp.ClientError:
        raise_core_error("contract_service_unavailable")

    return ContractServiceResponse.model_validate(response_data)


async def update_contract_status_for_job(job_id: int, action: str) -> dict:
    timeout = aiohttp.ClientTimeout(total=10)
    url = f"{CONTRACT_SERVICE_URL}/internal/contracts/job/{job_id}/{action}"

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.patch(
                url,
                headers=_internal_headers(),
            ) as response:
                if response.status >= 400:
                    error_body = await response.text()
                    print(
                        "Contract status update failed "
                        f"url={url}, status={response.status}, body={error_body}"
                    )
                    raise_core_error("contract_status_update_failed")
                print(
                    f"Contract status updated url={url}, status={response.status}"
                )
                return await response.json()
    except asyncio.TimeoutError:
        print(f"Contract status update timed out url={url}")
        raise_core_error("contract_service_timeout")
    except aiohttp.ClientError as exc:
        print(f"Contract status update unavailable url={url}, error={exc}")
        raise_core_error("contract_service_unavailable")


async def create_pending_payment(job_id: int, application_id: int) -> dict:
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{PAYMENT_SERVICE_URL}/payments/internal/jobs/{job_id}/pending",
                json={"application_id": application_id},
                headers=_internal_headers(),
            ) as response:
                if response.status >= 400:
                    raise_core_error("payment_creation_failed")
                return await response.json()
    except asyncio.TimeoutError:
        raise_core_error("payment_service_timeout")
    except aiohttp.ClientError:
        raise_core_error("payment_service_unavailable")


