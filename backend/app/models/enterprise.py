from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

from app.db.base import BaseIDModel
from app.models.role import RoleRelation
from app.models.scope import ScopeRelation

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.role import Role
    from app.models.scope import Scope
    from app.models.products import BaseProduct


class BaseEnterprise(SQLModel):
    """Represents a basic enterprise."""

    name: str = Field(description="Name of the enterprise.")
    accountable_email: str = Field(
        description="Email of the person accountable for the organization."
    )
    activity_type: str = Field(
        default="Others", description="Activity type of the enterprise."
    )


class Enterprise(BaseIDModel, BaseEnterprise, table=True):
    """Represents an enterprise."""

    __tablename__ = "enterprise"
    users: Optional[list["User"]] = Relationship(
        back_populates="enterprise",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    scopes: Optional[list["Scope"]] = Relationship(
        back_populates="enterprise",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    roles: Optional[list["Role"]] = Relationship(
        back_populates="enterprise",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    products: Optional[list["BaseProduct"]] = Relationship(
        back_populates="enterprise",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class EnterpriseRelation(BaseIDModel, BaseEnterprise):
    """Represents an enterprise relation."""


class EnterpriseWithHierarchy(EnterpriseRelation):
    roles: list["RoleRelation"]
    scopes: list["ScopeRelation"]


class EnterpriseResponse(SQLModel):
    """Represents a response from the enterprise."""

    status: int
    data: EnterpriseRelation
    message: str


class EnterpriseUpdate(SQLModel):
    """Represents an enterprise update."""

    name: Optional[str] = None
    accountable_email: Optional[str] = None
    activity_type: Optional[str] = None
