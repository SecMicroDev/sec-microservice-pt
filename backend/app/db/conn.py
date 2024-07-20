"""Module for database setup and utilities using SQLModel and SQLAlchemy."""

import sqlalchemy as sa
from sqlmodel import SQLModel, Session, create_engine

from . import settings as st


SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{st.DB_USER}:{st.DB_PASSWORD}@{st.DB_HOST}:5432/{st.DB_NAME}"
)


engine = create_engine(SQLALCHEMY_DATABASE_URL)


def create_db():
    """Creates a new database if it doesn't exist, and removes it if we are in testing mode."""

    if st.ENV == "test":
        SQLModel.metadata.drop_all(engine)

    # Create tables if they don't exist
    SQLModel.metadata.create_all(engine)


def get_db():
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


GUID_SERVER_DEFAULT_PSQL = sa.DefaultClause(sa.text("gen_random_uuid()"))
