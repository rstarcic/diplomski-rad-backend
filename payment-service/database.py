import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


import app.payments.models  # noqa: E402 — registers models with Base before create_all

PAYMENT_DB = os.getenv("PAYMENT_DB")

if not PAYMENT_DB:
    raise RuntimeError("PAYMENT_DB environment variable is not set")

engine = create_engine(PAYMENT_DB, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
