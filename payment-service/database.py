import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


PAYMENT_DB = os.getenv("PAYMENT_DB")

if not PAYMENT_DB:
    raise RuntimeError("PAYMENT_DB environment variable is not set")

engine = create_engine(PAYMENT_DB, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
