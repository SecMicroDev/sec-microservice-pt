from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session
from app.models.products import (
    BaseProduct,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)
from app.db.conn import get_db
from app.middlewares.auth import authenticate_user, authorize_user
from app.models.role import DefaultRole
from app.models.user import UserRead


router = APIRouter(prefix="/products")


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db_session: Session = Depends(get_db),
    current_user: UserRead = Depends(authenticate_user),
) -> ProductResponse:

    authorize_user(
        user=current_user,
        operation_scopes=["Patrimonial", "All"],
        operation_hierarchy_order=DefaultRole.get_default_hierarchy(
            DefaultRole.COLLABORATOR
        ),
    )

    if current_user.enterprise_id is None:
        raise HTTPException(status_code=403, detail="User has no enterprise")

    with db_session:
        db_product = BaseProduct(
            **product.model_dump(),
            created_by=current_user.id,
            enterprise_id=current_user.enterprise_id,
        )
        db_session.add(db_product)
        db_session.commit()
        db_session.refresh(db_product)

        return ProductResponse(**db_product.model_dump())


@router.get("/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: int,
    db_session: Session = Depends(get_db),
    current_user: UserRead = Depends(authenticate_user),
) -> ProductResponse:
    authorize_user(
        user=current_user,
        operation_scopes=["Patrimonial", "All"],
        operation_hierarchy_order=DefaultRole.get_default_hierarchy(
            DefaultRole.COLLABORATOR
        ),
    )

    with db_session:
        db_product = db_session.exec(
            select(BaseProduct)
            .where(BaseProduct.id == product_id)
            .where(BaseProduct.enterprise_id == current_user.enterprise_id)
        ).first()

        if db_product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductResponse(**db_product.model_dump())


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db_session: Session = Depends(get_db),
    current_user: UserRead = Depends(authenticate_user),
) -> ProductResponse:

    authorize_user(
        user=current_user,
        operation_scopes=["Patrimonial", "All"],
        operation_hierarchy_order=DefaultRole.get_default_hierarchy(
            DefaultRole.COLLABORATOR
        ),
        custom_checks=(
            not any(
                [k != "stock" for k in product.model_dump(exclude_unset=True).keys()]
            )
            or current_user.role.hierarchy
            <= DefaultRole.get_default_hierarchy(DefaultRole.MANAGER.value)
        ),
    )

    with db_session:
        db_product = db_session.exec(
            select(BaseProduct)
            .where(BaseProduct.id == product_id)
            .where(BaseProduct.enterprise_id == current_user.enterprise_id)
        ).first()

        if db_product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        for key, value in product.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)

        db_product.last_updated_by = current_user.id
        db_product.updated_at = datetime.now(timezone.utc)

        db_session.add(db_product)
        db_session.commit()
        db_session.refresh(db_product)

        print(f"Updated product: {db_product.model_dump()}")

        return ProductResponse(**db_product.model_dump())


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db_session: Session = Depends(get_db),
    current_user: UserRead = Depends(authenticate_user),
):
    authorize_user(
        user=current_user,
        operation_scopes=["Patrimonial", "All"],
        operation_hierarchy_order=DefaultRole.get_default_hierarchy(
            DefaultRole.MANAGER
        ),
    )

    with db_session:
        db_product = db_session.exec(
            select(BaseProduct)
            .where(BaseProduct.id == product_id)
            .where(BaseProduct.enterprise_id == current_user.enterprise_id)
        ).first()

        if db_product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        db_session.delete(db_product)
        db_session.commit()

    return {"detail": "Product deleted"}
