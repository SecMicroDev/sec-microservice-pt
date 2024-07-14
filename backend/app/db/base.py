"""
This module contains the `BaseIDModel` class, which is a base class for models with UUID primary key.

Attributes:
    uuid (Optional[UUID4]): The UUID primary key of the model.
"""

from typing import Optional
from sqlmodel import Field, SQLModel


class BaseIDModel(SQLModel):
    """
    Base class for models with UUID primary key.

    Attributes:
        uuid (Optional[UUID4]): The UUID primary key of the model.
    """

    id: Optional[int] | None = Field(
        # default_factory=uuid_pkg.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
