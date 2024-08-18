"""
This module defines the Scope model for storing scopes in the database.

The Scope model inherits from the BaseIDModel and BaseScope classes, 
which provide common fields and functionality.

It represents a scope stored in the database.

Attributes:
    name (str): The name of the scope.
    description (Optional[str]): The description of the scope.

"""

from enum import Enum
from typing import Any, Literal, Optional, TYPE_CHECKING, Union

from app.db.base import BaseIDModel
from sqlalchemy import Column, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel, or_, select
from sqlmodel.sql.expression import SelectOfScalar

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.enterprise import Enterprise


class BaseScope(SQLModel):
    """Represents a basic scope"""

    name: str = Field(
        description="Name of the scope.",
        sa_column=Column(String, index=True, nullable=False),
    )
    description: Optional[str] = Field(
        description="Description of the scope.", nullable=True
    )
    enterprise_id: int = Field(
        foreign_key="enterprise.id",
        description="The enterprise to which the scope belongs.",
        nullable=True,
    )

    @classmethod
    def get_scopes_by_enterprise_id(cls, enterprise_id: int) -> SelectOfScalar:
        return select(Scope).where(Scope.enterprise_id == enterprise_id)

    @classmethod
    def get_scopes_by_ids(cls, enterprise_id: int, ids: list[int]) -> SelectOfScalar:
        query = select(Scope).where(Scope.enterprise_id == enterprise_id)
        query = query.where(or_(*[Scope.id == id for id in ids]))
        return query

    @classmethod
    def get_scopes_by_names(
        cls, enterprise_id: int, names: list[str]
    ) -> SelectOfScalar:
        query = select(Scope).where(Scope.enterprise_id == enterprise_id)
        query = query.where(or_(*[Scope.name == name for name in names]))
        return query


class Scope(BaseIDModel, BaseScope, table=True):
    """Represents a scope stored in the database."""

    __tablename__ = "scope"
    __table_args__ = (UniqueConstraint("name", "enterprise_id"),)
    users: list["User"] = Relationship(back_populates="scope")
    enterprise: "Enterprise" = Relationship(back_populates="scopes")

    # @declared_attr
    # def scope_id(self):
    #     return synonym("id")


class ScopeRead(SQLModel):
    """Represents a scope read response."""

    id: int
    name: str


class ScopeCreate(BaseScope):
    """Represents a scope creation request."""


class ScopeUpdate(SQLModel):
    """Represents a scope update request."""

    name: Optional[str] = None
    description: Optional[str] = None


class DefaultScope(str, Enum):
    """Represents the default scopes available in the system."""

    ALL = "All"
    SELLS = "Sells"
    HUMAN_RESOURCE = "HumanResource"
    PATRIMONIAL = "Patrimonial"


class DefaultScopeSchema(SQLModel):
    name: DefaultScope
    description: str

    @classmethod
    def get_default_scopes(
        cls,
    ) -> dict[
        Union[
            Literal[DefaultScope.SELLS],
            Literal[DefaultScope.HUMAN_RESOURCE],
            Literal[DefaultScope.PATRIMONIAL],
            Literal[DefaultScope.ALL],
        ],
        dict[str, Any],
    ]:
        return {
            DefaultScope.SELLS: {
                "name": DefaultScope.SELLS.value,
                "description": "Sells scope from the enterprise.",
            },
            DefaultScope.HUMAN_RESOURCE: {
                "name": DefaultScope.HUMAN_RESOURCE.value,
                "description": "Human resource from the enterprise.",
            },
            DefaultScope.PATRIMONIAL: {
                "name": DefaultScope.PATRIMONIAL.value,
                "description": "Patrimonial scope from the enterprise.",
            },
            DefaultScope.ALL: {
                "name": DefaultScope.ALL.value,
                "description": "All scopes from the enterprise.",
            },
        }


class ScopeRelation(SQLModel):
    """Represents a scope in the User model."""

    id: Optional[int] = None
    name: str
