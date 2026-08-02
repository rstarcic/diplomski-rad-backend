from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import models  # noqa: F401
from app.contracts.router import router as contracts_router
from app.internal.router import router as internal_router
from database import engine, init_db
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncGenerator[None, None]:
    init_db()

    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="Contract Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(contracts_router)
app.include_router(internal_router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="localhost",
        port=8002,
        reload=True,
    )
