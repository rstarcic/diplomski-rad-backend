import asyncio
import os
from contextlib import asynccontextmanager
from datetime import timedelta

import app.models
import uvicorn
from app.internal.router import router as internal_router
from app.payments.router import router as payments_router
from app.payments.service import expire_pending_job_payments
from database import SessionLocal, init_db
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv(override=False)


PAYMENT_PENDING_TIMEOUT_MINUTES = int(
    os.getenv("PAYMENT_PENDING_TIMEOUT_MINUTES", "4320")
)

PAYMENT_EXPIRATION_CHECK_SECONDS = int(
    os.getenv("PAYMENT_EXPIRATION_CHECK_SECONDS", "60")
)


def run_payment_expiration_check() -> None:
    db = SessionLocal()

    try:
        expired_count = expire_pending_job_payments(
            db,
            timedelta(minutes=PAYMENT_PENDING_TIMEOUT_MINUTES),
        )

        if expired_count:
            print(f"Marked {expired_count} pending payment(s) as overdue.")
    except Exception as exc:
        print(f"Payment expiration check failed: {exc}")
    finally:
        db.close()


async def payment_expiration_worker() -> None:
    while True:
        await asyncio.to_thread(run_payment_expiration_check)
        await asyncio.sleep(PAYMENT_EXPIRATION_CHECK_SECONDS)


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kreira tablice definirane SQLAlchemy modelima.
    init_db()

    expiration_task = asyncio.create_task(payment_expiration_worker())

    try:
        yield
    finally:
        expiration_task.cancel()

        try:
            await expiration_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Payment Service",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    first_error = exc.errors()[0]

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "validation_error",
                "message": first_error.get(
                    "msg",
                    "Invalid input.",
                ).replace("Value error, ", ""),
                "field": first_error.get(
                    "loc",
                    [None],
                )[-1],
            }
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(payments_router)
app.include_router(internal_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )
