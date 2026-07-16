from database import Base, engine
from fastapi import FastAPI
from models import Contract
from router import internal_router, router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Contract Service",
    version="1.0.0",
)

app.include_router(internal_router)
app.include_router(router)


@app.get("/health")
def health_check():
    return {
        "service": "contract-service",
        "status": "healthy",
    }
