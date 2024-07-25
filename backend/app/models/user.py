"""  User model package """

from typing import Optional, Tuple
from datetime import datetime as dt, timezone
from pydantic import EmailStr
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel, Column, col, select, and_
from sqlmodel.sql.expression import Select, SelectOfScalar

from app.models.enterprise import Enterprise, EnterpriseRelation
from app.db.base import BaseIDModel

from app.models.products import BaseProduct
from app.models.role import Role
from app.models.scope import Scope
from app.models.api_response import APIResponse

from app.models.role import RoleRelation
from app.models.scope import ScopeRelation


class BaseUser(SQLModel):
    """Represents a user stored in the database."""

    username: str = Field(
        description="Username for the user.",
        sa_column=Column(String, index=True),
    )
    email: EmailStr = Field(
        sa_column=Column(String, unique=True, index=True),
        description="Email address of the user.",
    )
    full_name: Optional[str] = Field(
        default=None, description="Full name of the user.", nullable=True
    )

    def query_scopes_roles(
        self, roles_ids: list[int] = [], scopes_ids: list[int] = []
    ) -> Select[Tuple[Enterprise, Scope, Role]]:
        query = select(Enterprise, Scope, Role).where(
            Enterprise.id == self.enterprise_id
        )

        if roles_ids and len(roles_ids) > 0:
            query = query.where(col(Role.id).in_(roles_ids))

        if scopes_ids and len(scopes_ids) > 0:
            query = query.where(col(Scope.id).in_(scopes_ids))

        if roles_ids and len(roles_ids) > 0:
            query.join(Role, and_(Role.enterprise_id == Enterprise.id))

        if scopes_ids and len(scopes_ids) > 0:
            query.join(Scope, and_(Scope.enterprise_id == Enterprise.id))

        return query

    def query_scope_role_by_id(
        self, role_id: int, scope_id: int
    ) -> Select[Tuple[Enterprise, Scope, Role]]:
        return (
            select(Enterprise, Scope, Role)
            .where(
                (Enterprise.id == self.enterprise_id)
                & (Scope.id == scope_id)
                & (Role.id == role_id)
            )
            .join(Scope)
            .join(Role)
        )

    def query_scope_role_by_name(
        self, role_name: str, scope_name: str
    ) -> Select[tuple]:
        return (
            select(Enterprise, Scope, Role)
            .where(
                (Enterprise.id == self.enterprise_id)
                & (Scope.name == scope_name)
                & (Role.name == role_name)
            )
            .join(Scope)
            .join(Role)
        )


class User(BaseIDModel, BaseUser, table=True):
    """
    Represents a user in the system.

    Attributes:
        created_at (datetime): Timestamp of when the user was registered.
        role_id (int, optional): ID of the role associated with the user.
        scope_id (int, optional): ID of the scope associated with the user.
        enterprise_id (int, optional): ID of the enterprise associated with the user.
        role (Role, optional): Role object associated with the user.
        scope (Scope, optional): Scope object associated with the user.
        enterprise (Enterprise, optional): Enterprise object associated with the user.
    """

    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("username", "enterprise_id"),)
    created_at: dt = Field(
        description="Timestamp of when the user was registered.",
        default_factory=lambda: dt.now(timezone.utc),
    )
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    scope_id: Optional[int] = Field(
        default=None, foreign_key="scope.id", nullable=False
    )
    role: Optional[Role] = Relationship(back_populates="users")
    scope: Optional[Scope] = Relationship(back_populates="users")
    enterprise: Optional[Enterprise] = Relationship(back_populates="users")
    enterprise_id: int | None = Field(foreign_key="enterprise.id", nullable=False)
    products: Optional[list["BaseProduct"]] = Relationship(
        sa_relationship=RelationshipProperty(
            "BaseProduct",
            back_populates="user_created",
            foreign_keys="[BaseProduct.created_by]",
        )
    )

    updates: Optional[list["BaseProduct"]] = Relationship(
        sa_relationship=RelationshipProperty(
            "BaseProduct",
            back_populates="user_updated",
            foreign_keys="[BaseProduct.last_updated_by]",
        )
    )

    def get_all(self) -> SelectOfScalar:
        return select(User).where(User.enterprise_id == self.enterprise_id)


class UserCreate(BaseUser):
    """Represents a user creation request."""

    password: str
    enterprise_id: int
    role_id: Optional[int] = None
    scope_id: Optional[int] = None
    role_name: Optional[str] = None
    scope_name: Optional[str] = None


class UserUpdate(SQLModel):
    """Represents a user update request."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    scope_name: Optional[str] = None
    scope_id: Optional[int] = None


class UserRead(BaseUser):
    """Represents a user read response."""

    id: int
    created_at: dt
    enterprise_id: int | None = None
    edited_at: Optional[dt] = None
    role: "RoleRelation"
    scope: "ScopeRelation"
    enterprise: "EnterpriseRelation"


class UserListResponse(APIResponse):
    """Represents a list of users."""

    data: list[UserRead] = []


class UserResponse(APIResponse):
    """Represents a user response."""

    data: UserRead
