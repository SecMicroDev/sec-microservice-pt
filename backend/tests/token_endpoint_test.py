import pytest
from jose import JWTError
from jose.exceptions import JWSSignatureError
from fastapi import HTTPException
from unittest.mock import patch

from app.auth.jwt_utils import create_jwt_token
from app.models.user import UserRead
from app.models.scope import DefaultScope, DefaultScopeSchema, ScopeRelation
from app.models.role import DefaultRole, DefaultRoleSchema, RoleRelation
from app.middlewares.auth import authenticate_user, authorize_user


def get_user_data():
    return {
        "id": 1,
        "username": "test",
        "email": "testuser@test.mail.com",
        "created_at": "2022-01-01T00:00:00",
        "edited_at": "2022-01-02T00:00:00",
        "role": {
            "id": 1,
            **(DefaultRoleSchema.get_default_roles()[DefaultRole.MANAGER]),
        },
        "scope": {
            "id": 1,
            **(DefaultScopeSchema.get_default_scopes()[DefaultScope.PATRIMONIAL]),
        },
        "enterprise": {
            "id": 1,
            "name": "enterprise1",
            "accountable_email": "test@test.mail.com",
        },
    }


def create_valid_token(expires=2):

    user_data = get_user_data()
    print(str(user_data))
    return create_jwt_token(user_data, expires=expires)


def test_authenticate_user_valid_token():
    # with patch('app.auth.decode_jwt_token') as mock_decode:
    token = create_valid_token()
    user = authenticate_user(token)
    print(str(user))
    assert user.username == "test"
    assert isinstance(user, UserRead)


def test_authenticate_user_expired_token():
    # with patch('app.auth.decode_jwt_token') as mock_decode:
    # mock_decode.side_effect = JWTError("Expired token")
    token = create_valid_token(-10)

    with pytest.raises(HTTPException) as exc_info:
        authenticate_user(token)
    assert exc_info.value.status_code == 401


def test_authenticate_user_invalid_signature():
    with patch("app.auth.jwt_utils.decode_jwt_token") as mock_decode:
        mock_decode.side_effect = JWSSignatureError("Invalid signature")
        with pytest.raises(HTTPException) as exc_info:
            authenticate_user("invalid_signature_token")
        assert exc_info.value.status_code == 401


def test_authorize_user_valid_scope():
    user = UserRead(**get_user_data())
    user.role = RoleRelation(**DefaultRoleSchema.get_default_roles()[DefaultRole.OWNER])
    user.scope = ScopeRelation(
        **DefaultScopeSchema.get_default_scopes()[DefaultScope.ALL]
    )
    assert authorize_user(user, ["All"], 1) == user


def test_authorize_user_invalid_scope():
    user_read = get_user_data()
    user_read.update({"scope": {"name": "Selling"}})
    user = UserRead(**user_read)
    with pytest.raises(HTTPException) as exc_info:
        authorize_user(user, ["All"], 1)
    assert exc_info.value.status_code == 403


def test_authorize_user_invalid_role():
    user = UserRead(**get_user_data())

    user.role = RoleRelation(
        **DefaultRoleSchema.get_default_roles()[DefaultRole.COLLABORATOR]
    )
    user.scope = ScopeRelation(
        **DefaultScopeSchema.get_default_scopes()[DefaultScope.SELLS]
    )

    with pytest.raises(HTTPException) as exc_info:
        authorize_user(user, ["Selling"], 2)
    assert exc_info.value.status_code == 403


# kiseRoleSchema(role=DefaultEnterpriseRole.MANAGER),
#             DefaultEnterpriseRoleSchema(role=DefaultEnterpriseRole.EMPLOYEE),
#             DefaultEnterpriseRoleSchema(role=DefaultEnterpriseRole.SUPERVISOR),
#         ]
#         scopes = [
#             DefaultEnterpriseScopeSchema(scope=DefaultEnterpriseScope.ALL),
#             DefaultEnterpriseScopeSchema(scope=DefaultEnterpriseScope.HUMAN_RESOURCE),
#             DefaultEnterpriseScopeSchema(scope=DefaultEnterpriseScope.SALES),
#             DefaultEnterpriseScopeSchema(scope=DefaultEnterpriseScope.STOCK),
#         ]

#         enterprise = EnterpriseCreate(
#             name="Jarucucu",
#             accountable_email="testorg@test.mail.com",
#         )
#         insert_enterprise = Enterprise.model_validate(enterprise)
#         insert_enterprise.roles = roles
#         insert_enterprise.scopes = roles

#         # enterprise = session.exec(select(Enterprise).where(Enterprise.name == "Jarucucu")).one()

#         user = FullUser(
#             username="testuser",
#             email="test@test.mail.com",
#             hashed_password="hashedpassword",
#             role=roles[0],
#             scope=scopes[0],
#             enterprise=enterprise,
#         )

#         session.add(user)
#         session.commit()


# def test_login_for_access_token(test_client: TestClient):
#     # Test case with valid credentials
#     response = test_client.post(
#         "/token", data={"username": "testuser", "password": "hashedpassword"}
#     )

#     assert response.status_code == 200
#     assert "access_token" in response.json()
#     assert response.json()["token_type"] == "bearer"

#     # Test case with incorrect credentials
#     response = test_client.post(
#         "/token", data={"username": "testuser", "password": "incorrectpassword"}
#     )
#     assert response.status_code == 401
#     assert "access_token" not in response.json()
#     assert response.json()["detail"] == "Incorrect username or password"
