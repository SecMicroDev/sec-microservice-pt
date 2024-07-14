"""Module for database setup and utilities using SQLModel and SQLAlchemy."""

from collections.abc import Generator
from sqlmodel import Session, create_engine, SQLModel
import sqlalchemy as sa


from . import settings as st


def setup_guids_postgresql(engine) -> None:
    with Session(engine) as session:
        session.exec('create EXTENSION if not EXISTS "pgcrypto"')
        session.commit()


def create_db():
    """Creates a new database if it doesn't exist, and removes it if we are in testing mode."""
    pass


def get_db() -> Generator:
    """Gets a new database session and closes it when done.

    Yields:
        Session: a new database session
    """

    session = Session(autocommit=False, autoflush=False, bind=engine)
    try:
        yield session
    finally:
        if session.is_active:
            session.close()


SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{st.DB_USER}:{st.DB_PASSWORD}@{st.DB_HOST}:5432/{st.DB_NAME}"
)

GUID_SERVER_DEFAULT_PSQL = sa.DefaultClause(sa.text("gen_random_uuid()"))

engine = create_engine(SQLALCHEMY_DATABASE_URL)
