import os
from contextlib import asynccontextmanager

import uvicorn
from app.router import router as payments_router
from database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Payment Service", prefix="payments", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router, prefix="/payments")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="localhost", port=8002, reload=True)
