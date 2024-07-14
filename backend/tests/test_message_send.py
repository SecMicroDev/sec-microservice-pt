import json
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from app.messages.client import AsyncSender
from app.models.enterprise import BaseEnterprise, Enterprise, EnterpriseUpdate
from app.models.user import (
    FirstUserCreate,
    UserCreate,
    UserRead,
    UserUpdate,
    UserUpdateMe,
)
from app.router.utils import EnterpriseUpdateWithId, UserEvents, UserUpdateWithId


@patch.object(AsyncSender, "publish")
def test_create_user(mock_publish: Mock, test_client_auth_default_with_broker):
    client: TestClient = test_client_auth_default_with_broker
    user = UserCreate(
        username="testuser2",
        password="testpassword2",
        email="emailtest2@test.com.br",
        enterprise_id=1,
        role_id=1,
        scope_id=1,
    )

    mock_publish.return_value = AsyncMock()

    response = client.post("/users/", json=user.model_dump())
    user = UserRead(**response.json()["data"])
    user_dict = json.loads(user.model_dump_json())

    mock_publish.assert_called_once()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                assert all_info["event"] == UserEvents.USER_CREATED.value
                x_dict = all_info["data"]

                def compare_val(k, v):
                    return v == user_dict[k] if k in user_dict else False

                return all(
                    [
                        compare_val(key, val) if key in user_dict.keys() else False
                        for key, val in x_dict.items()
                    ]
                )

            return False
        except json.JSONDecodeError:
            return False

    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))
    assert response.status_code == 201


@patch.object(AsyncSender, "publish")
def test_update_current_user(mock_publish: Mock, test_client_auth_default_with_broker):
    client: TestClient = test_client_auth_default_with_broker
    user = UserUpdateMe(
        username="testuser2",
        password="testpassword2",
        email="emailtest2@test.com.br",
    )

    mock_publish.return_value = AsyncMock()

    response = client.put("/users/me", json=user.model_dump())

    user = UserUpdateWithId(**response.json()["data"])
    user_dict = json.loads(user.model_dump_json())

    mock_publish.assert_called_once()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                # assert all_info["event"] == UserEvents.USER_UPDATED.value
                x_dict = all_info["data"]

                def compare_val(k, v):
                    return v == user_dict[k] if k in user_dict else False

                return all(
                    [
                        compare_val(key, val) if key in user_dict.keys() else False
                        for key, val in x_dict.items()
                    ]
                )

            return False
        except json.JSONDecodeError:
            return False

    assert response.status_code == 200
    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))


@patch.object(AsyncSender, "publish")
def test_update_user(mock_publish: Mock, test_client_auth_default_with_broker):
    client: TestClient = test_client_auth_default_with_broker
    user_id = 1  # replace with a valid user id
    user = UserUpdate(
        username="testuser2",
        password="testpassword2",
        email="emailtest2@test.com.br",
        role_id=2,
    )

    mock_publish.return_value = AsyncMock()

    response = client.put(f"/users/{user_id}", json=user.model_dump())

    assert response.status_code == 200

    user = UserUpdateWithId(**response.json()["data"])
    user_dict = json.loads(user.model_dump_json())

    mock_publish.assert_called_once()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                x_dict = all_info["data"]

                def compare_val(k, v):
                    return v == user_dict[k] if k in user_dict else False

                return all(
                    [
                        compare_val(key, val) if key in user_dict.keys() else False
                        for key, val in x_dict.items()
                    ]
                )

            return False
        except json.JSONDecodeError:
            return False

    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))


@patch.object(AsyncSender, "publish")
def test_delete_user(mock_publish: Mock, test_client_auth_default_with_broker):
    client: TestClient = test_client_auth_default_with_broker
    user_id = 1  # replace with a valid user id

    mock_publish.return_value = AsyncMock()

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 200

    mock_publish.assert_called_once()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                x_dict = all_info["data"]
                return x_dict["id"] == user_id
            return False
        except json.JSONDecodeError:
            return False

    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))


@patch.object(AsyncSender, "publish")
def test_create_enterprise(mock_publish: Mock, test_client_auth_default_with_broker):
    client: TestClient = test_client_auth_default_with_broker
    enterprise = BaseEnterprise(
        name="testenterprise2", accountable_email="emailchange@test.com"
    )

    user = FirstUserCreate(
        username="testuser",
        password="testpassword",
        email="emailtest@test.com.br",
    )

    mock_publish.return_value = AsyncMock()

    response = client.post(
        "/enterprise/signup",
        json={"enterprise": enterprise.model_dump(), "user": user.model_dump()},
    )

    assert response.status_code == 200

    mock_publish.assert_called()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                x_dict = all_info["data"]
                return (
                    x_dict["enterprise"]["name"] == enterprise.name
                    and x_dict["username"] == user.username
                )
            return False
        except json.JSONDecodeError:
            return False

    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))


@patch.object(AsyncSender, "publish")
def test_update_enterprise(mock_publish: Mock, test_client_auth_default_with_broker):
    client: TestClient = test_client_auth_default_with_broker
    enterprise = EnterpriseUpdate(
        name="testenterprise3",
        activity_type="Games",
    )

    mock_publish.return_value = AsyncMock()

    response = client.put("/enterprise", json=enterprise.model_dump())

    assert response.status_code == 200

    enterprise = EnterpriseUpdateWithId(**response.json()["data"])
    enterprise_dict = json.loads(enterprise.model_dump_json())

    mock_publish.assert_called_once()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                x_dict = all_info["data"]

                def compare_val(k, v):
                    return v == enterprise_dict[k] if k in enterprise_dict else False

                return all(
                    [
                        (
                            compare_val(key, val)
                            if key in enterprise_dict.keys()
                            else False
                        )
                        for key, val in x_dict.items()
                    ]
                )

            return False
        except json.JSONDecodeError:
            return False

    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))


@patch.object(AsyncSender, "publish")
def test_delete_enterprise(
    mock_publish: Mock,
    test_client_auth_default_with_broker,
    enterprise_role_scope: dict[str, Any],
):
    client: TestClient = test_client_auth_default_with_broker
    enterprise: Enterprise = enterprise_role_scope["enterprise"]

    mock_publish.return_value = AsyncMock()

    response = client.delete("/enterprise")

    assert response.status_code == 200

    mock_publish.assert_called_once()

    def compare_dict(x: Any):
        try:
            if isinstance(x, str):
                all_info = json.loads(x)
                x_dict = all_info["data"]
                return x_dict["id"] == enterprise.id
            return False
        except json.JSONDecodeError:
            return False

    assert any(map(lambda x: compare_dict(x), mock_publish.call_args.args))
