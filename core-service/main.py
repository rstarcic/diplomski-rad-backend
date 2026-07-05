import os
from contextlib import asynccontextmanager

import uvicorn
from app.jobs.router import router as jobs_router
from app.profiles.router import router as profiles_router
from database import init_db
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(override=True)


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Core Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles_router, prefix="/profiles")
app.include_router(jobs_router, prefix="/jobs")

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8001, reload=True)
