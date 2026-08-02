import os
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://localhost:8001")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


async def notify_job_contract_activated(job_id: int) -> None:
    if not INTERNAL_SECRET:
        _sync_error()

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.patch(
                f"{CORE_SERVICE_URL}/internal/jobs/{job_id}/contract-activated",
                headers={"x-internal-secret": INTERNAL_SECRET},
            ) as response:
                if response.status >= status.HTTP_400_BAD_REQUEST:
                    _sync_error()
    except (TimeoutError, aiohttp.ClientError):
        _sync_error()


def _sync_error() -> None:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "code": "job_activation_sync_failed",
            "message": (
                "The contract was signed, but the job status could not be synchronized. "
                "Please retry."
            ),
            "field": "status",
        },
    )
