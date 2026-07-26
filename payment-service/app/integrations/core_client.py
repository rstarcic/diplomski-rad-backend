import asyncio
import os

import aiohttp
from fastapi import status

from app.dependencies import INTERNAL_SECRET
from app.integrations.schemas import ContractorProfile
from errors import payment_error, raise_payment_error


CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")


async def get_contractor_profile(user_id: int) -> ContractorProfile:
    if not INTERNAL_SECRET:
        raise_payment_error("internal_authentication_unavailable")

    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{CORE_SERVICE_URL}/internal/profiles/{user_id}/contractor",
                headers={"x-internal-secret": INTERNAL_SECRET},
            ) as response:
                if response.status == status.HTTP_404_NOT_FOUND:
                    raise_payment_error("contractor_profile_not_found")
                if response.status >= 400:
                    raise_payment_error("core_service_failed")
                data = await response.json()
    except asyncio.TimeoutError as exc:
        raise payment_error("core_service_timeout") from exc
    except aiohttp.ClientError as exc:
        raise payment_error("core_service_unavailable") from exc

    return ContractorProfile.model_validate(data)
