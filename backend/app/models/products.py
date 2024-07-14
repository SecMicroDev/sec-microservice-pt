from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel
from app.db.base import BaseIDModel

if TYPE_CHECKING:
    from app.models.enterprise import Enterprise
    from app.models.user import User


class ProductBase(BaseIDModel):
    name: str = Field(description="Name of the product.", max_length=120, index=True, unique=True)
    cost: float = Field(description="Cost of the product.", ge=0.0)
    description: Optional[str] = Field(default=None, max_length=450)
    stock: int = Field(description="Stock of the product.", ge=0, default=0)
    enterprise_id: Optional[int] = Field(
        foreign_key="enterprise.id",
        index=True,
    )


class BaseProduct(ProductBase, table=True):
    """Represents a product stored in the database."""

    price: Optional[float] = Field(description="Price of the product.", ge=0.0, default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    created_by: Optional[int] = Field(foreign_key="user.id", description="User ID that created the product.")
    last_updated_by: Optional[int] = Field(foreign_key="user.id", description="User ID that last updated the product.")
    user_updated: Optional["User"] = Relationship(sa_relationship=RelationshipProperty(
        "User",
        back_populates="updates",
        foreign_keys="[BaseProduct.last_updated_by]",
    ))
    user_created: Optional["User"] = Relationship(sa_relationship=RelationshipProperty(
        "User",
        back_populates="products",
        foreign_keys="[BaseProduct.created_by]"
    ))
    enterprise: "Enterprise" = Relationship(back_populates="products")

    __tablename__ = "product"
    __table_args__ = (UniqueConstraint("name", "enterprise_id"),)


class ProductCreate(SQLModel):
    cost: float
    name: str
    description: Optional[str]
    stock: int


class ProductUpdate(SQLModel):
    cost:        Optional[float] | None = None
    name:        Optional[str]   | None = None
    stock:       Optional[int]   | None = None
    price:       Optional[float] | None = None
    description: Optional[str]   | None = None


class ProductResponse(ProductBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

