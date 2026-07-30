import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


CORE_DB = os.getenv("CORE_DB")

if not CORE_DB:
    raise RuntimeError("CORE_DB environment variable is not set")

engine = create_engine(CORE_DB, pool_pre_ping=True)

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
