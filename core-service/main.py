import os
from contextlib import asynccontextmanager

import uvicorn
from app.applications.router import router as applications_router
from app.jobs.router import router as jobs_router
from app.internal.router import router as internal_router
from app.negotiations.router import router as negotiations_router
from app.profiles.router import router as profiles_router
from app.reviews.router import router as reviews_router
from app.dashboard.router import router as dashboard_router
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
app.include_router(applications_router)
app.include_router(negotiations_router, prefix="/negotiations")
app.include_router(reviews_router)
app.include_router(dashboard_router)
app.include_router(internal_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8001, reload=True)
