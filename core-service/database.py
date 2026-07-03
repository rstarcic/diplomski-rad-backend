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
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE profiles "
                "ADD COLUMN IF NOT EXISTS profile_picture_blob BYTEA"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE profiles "
                "ADD COLUMN IF NOT EXISTS profile_picture_content_type VARCHAR(100)"
            )
        )
