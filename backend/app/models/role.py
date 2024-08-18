"""
This module defines the Role model and its base class.
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


class BaseRole(SQLModel):
    """Represents a role stored in the database."""

    name: str = Field(
        description="Name of the role.",
        sa_column=Column(String, index=True, nullable=False),
    )
    description: Optional[str] = Field(
        description="Description of the role.", nullable=True
    )
    hierarchy: int = Field(nullable=False)
    enterprise_id: int = Field(
        foreign_key="enterprise.id",
        description="The enterprise to which the scope belongs.",
        nullable=True,
    )

    @classmethod
    def get_roles_by_enterprise_id(cls, enterprise_id: int) -> SelectOfScalar:
        return select(Role).where(Role.enterprise_id == enterprise_id)

    @classmethod
    def get_roles_by_ids(cls, enterprise_id: int, ids: list[int]) -> SelectOfScalar:
        query = select(Role).where(Role.enterprise_id == enterprise_id)
        query = query.where(or_(*[Role.id == id for id in ids]))
        return query

    @classmethod
    def get_roles_by_names(cls, enterprise_id: int, names: list[str]) -> SelectOfScalar:
        query = select(Role).where(Role.enterprise_id == enterprise_id)
        query = query.where(or_(*[Role.name == name for name in names]))
        return query


class Role(BaseIDModel, BaseRole, table=True):
    """Represents a role stored in the database."""

    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("name", "enterprise_id"),)
    users: list["User"] = Relationship(back_populates="role")
    enterprise: "Enterprise" = Relationship(back_populates="roles")


class RoleCreate(BaseRole):
    """Represents a role creation request."""


class RoleRead(BaseRole):
    """Represents a role read response."""


class DefaultRole(str, Enum):
    OWNER = "Owner"
    MANAGER = "Manager"
    COLLABORATOR = "Collaborator"

    @classmethod
    def get_default_hierarchy(cls, role: str) -> int:

        return {
            DefaultRole.OWNER.value: 1,
            DefaultRole.MANAGER.value: 2,
            DefaultRole.COLLABORATOR.value: 3,
        }[role]


class DefaultRoleSchema(SQLModel):
    name: DefaultRole
    description: str

    @classmethod
    def get_default_roles(
        cls,
    ) -> dict[
        Union[
            Literal[DefaultRole.OWNER],
            Literal[DefaultRole.COLLABORATOR],
            Literal[DefaultRole.MANAGER],
        ],
        dict[str, Any],
    ]:
        return {
            DefaultRole.OWNER: {
                "name": DefaultRole.OWNER.value,
                "description": "The owner of the enterprise.",
                "hierarchy": 1,
            },
            DefaultRole.COLLABORATOR: {
                "name": DefaultRole.COLLABORATOR.value,
                "description": "A collaborator of the enterprise.",
                "hierarchy": 3,
            },
            DefaultRole.MANAGER: {
                "name": DefaultRole.MANAGER.value,
                "description": "A manager of the enterprise.",
                "hierarchy": 2,
            },
        }


class RoleUpdate(SQLModel):
    """Represents a role update request."""

    name: Optional[str] = None
    description: Optional[str] = None
    hierarchy: Optional[int] = None


class RoleRelation(SQLModel):
    """Represents the role in a User model."""

    id: Optional[int] = None
    name: str
    hierarchy: int
