from typing import Any
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.products import BaseProduct, ProductCreate, ProductUpdate, ProductResponse

def test_create_product(
    test_client_authenticated_default: TestClient,
    db_session: Session,
):
    test_client = test_client_authenticated_default

    product_data = ProductCreate(
        name="Test Product 3",
        description="A product for testing purposes",
        stock=10,
        cost=50.0,
    ).model_dump()

    response = test_client.post(
    "/products/",
    json=product_data,
)
    assert response.status_code == status.HTTP_200_OK

    product_response = response.json()

    assert product_response is not None

    product_id = product_response.get("id")

    assert product_id is not None

    assert product_response.get("name") == product_data["name"]
    assert product_response.get("description") == product_data["description"]
    assert product_response.get("stock") == product_data["stock"]

    db_product = db_session.get(BaseProduct, product_id)
    assert db_product is not None
    assert db_product.name == product_data["name"]
    assert db_product.description == product_data["description"]
    assert db_product.stock == product_data["stock"]


def test_read_product(
    test_client_authenticated_default: TestClient,
    create_default_user: dict[str, Any],
):
    test_client = test_client_authenticated_default

    product_id = create_default_user["products"][0].id

    response = test_client.get(f"/products/{product_id}")
    assert response.status_code == status.HTTP_200_OK

    product_response = response.json()
    assert product_response is not None
    assert product_response["id"] == product_id
    assert product_response["name"] == create_default_user["products"][0].name
    assert product_response["description"] == create_default_user["products"][0].description
    assert product_response["stock"] == create_default_user["products"][0].stock


def test_update_product(
    test_client_authenticated_default: TestClient,
    db_session: Session,
    create_default_user: dict[str, Any],
):
    test_client = test_client_authenticated_default

    product_id = create_default_user["products"][0].id
    update_data = ProductUpdate(
        name="Updated Product Name",
        description="Updated Description"
    ).model_dump(exclude_none=True)

    response = test_client.put(
        f"/products/{product_id}",
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK

    updated_product_response = response.json()

    assert updated_product_response is not None
    assert updated_product_response["id"] == product_id
    assert updated_product_response["name"] == update_data["name"]
    assert updated_product_response["description"] == update_data["description"]

    db_product = db_session.get(BaseProduct, product_id)
    assert db_product is not None
    assert db_product.name == update_data["name"]
    assert db_product.description == update_data["description"]


def test_delete_product(
    test_client_authenticated_default: TestClient,
    db_session: Session,
    create_default_user: dict[str, Any],
):
    test_client = test_client_authenticated_default

    product_id = create_default_user["products"][0].id

    response = test_client.delete(f"/products/{product_id}")
    assert response.status_code == status.HTTP_200_OK

    db_product = db_session.get(BaseProduct, product_id)
    assert db_product is None

# def test_query_products(
#     test_client_authenticated_default: TestClient,
#     create_default_user: dict[str, Any],
# ):
#     test_client = test_client_authenticated_default

#     response = test_client.get("/products/")
#     assert response.status_code == status.HTTP_200_OK

#     products_data = response.json().get("data")
#     assert products_data is not None
#     assert len(products_data) == len(create_default_user["products"])

#     for i, product_data in enumerate(products_data):
#         assert product_data["id"] == create_default_user["products"][i].id
#         assert product_data["name"] == create_default_user["products"][i].name
#         assert product_data["description"] == create_default_user["products"][i].description
#         assert product_data["price"] == create_default_user["products"][i].price
#         assert product_data["stock"] == create_default_user["products"][i].stock

