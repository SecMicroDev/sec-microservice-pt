from datetime import datetime, timedelta
from typing import Any, Union
from unittest.mock import patch

from fastapi import HTTPException
import jwt
from jwt.exceptions import InvalidSignatureError
import pytest

from app.middlewares.auth import authenticate_user, authorize_user
from app.models.role import DefaultRole, DefaultRoleSchema, RoleRelation
from app.models.scope import DefaultScope, DefaultScopeSchema, ScopeRelation
from app.models.user import UserRead


TEST_KEY = """
-----BEGIN PRIVATE KEY-----
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
7HrmRa7ofO8NFWB0IpDH+WQzineHWA==
-----END PRIVATE KEY-----
"""


DEFAULT_OPTIONS = {
    "iss": "openferp.org",
}


JWT_SECRET_ENCODE_KEY = TEST_KEY


DEFAULT_ENCODE_CONFIG = {"JWT_KEY": JWT_SECRET_ENCODE_KEY, "JWT_ALGO": "RS256"}


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


def create_jwt_token(
    payload: dict,
    expires: int = 3 * 60,
    config: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed token with a defined algorithm and secret
    for signature. The payload is a dict and the expire time is in minutes
    """

    if config is None:
        config = DEFAULT_ENCODE_CONFIG

    current_default_options: dict[str, Union[str, datetime]] = {
        **DEFAULT_OPTIONS,
        "iat": datetime.now(),
    }

    return jwt.encode(
        {
            "exp": (datetime.now() + timedelta(seconds=expires)).timestamp(),
            "sub": str(payload).replace("'", '"'),
            **current_default_options,
        },
        config["JWT_KEY"],
        config["JWT_ALGO"],
    )


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
        mock_decode.side_effect = InvalidSignatureError("Invalid signature")
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
