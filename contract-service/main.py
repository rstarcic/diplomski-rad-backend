from app.contracts.router import router as contracts_router
from app.internal.router import router as internal_router
from database import Base, engine
from fastapi import FastAPI
from models import Contract

app = FastAPI(title="Contract Service")


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Contract Service",
    version="1.0.0",
)

app.include_router(contracts_router)
app.include_router(internal_router)


@app.get("/health")
def health_check():
    return {
        "service": "contract-service",
        "status": "healthy",
    }
