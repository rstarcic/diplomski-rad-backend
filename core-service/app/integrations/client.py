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

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

CONTRACT_SERVICE_URL = os.getenv(
    "CONTRACT_SERVICE_URL",
    "http://localhost:8003",
)
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


