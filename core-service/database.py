import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


CORE_DB = os.getenv("CORE_DB")

if not CORE_DB:
    raise RuntimeError("CORE_DB environment variable is not set")

engine = create_engine(CORE_DB, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    # Compatibility migration for databases created before reviews were
    # associated with jobs. New installations already have this column.
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE reviews "
                "ADD COLUMN IF NOT EXISTS job_id INTEGER REFERENCES jobs(id)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_reviews_job_reviewer "
                "ON reviews (job_id, reviewer_id)"
            )
        )
