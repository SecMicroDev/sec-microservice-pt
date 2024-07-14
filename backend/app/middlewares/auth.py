from typing import Annotated, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.auth.jwt_utils import JWTValidationError, decode_jwt_token
from app.models.user import UserRead
from app.models.scope import DefaultScope


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserRead:
    """
    Authenticates the user based on the provided token.

    Args:
        token (str): The JWT token used for authentication.

    Returns:
        UserRead: The authenticated user's information.

    Raises:
        HTTPException: If the credentials cannot be validated.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt_token(token)

        if payload is None or "sub" not in payload:
            raise credentials_exception

        user: dict[str, Any] = payload.get("sub", {})
        if user is None:
            raise credentials_exception
        print(user)
        token_data = UserRead(**user)

        return token_data
    except JWTError as ex:
        raise credentials_exception from ex
    except JWTValidationError as ex:
        raise credentials_exception from ex


def authorize_user(
    user: UserRead = Depends(authenticate_user),
    operation_scopes: list[str] = ["All"],
    operation_hierarchy_order: int = 1,
    custom_checks: bool | None = None,
) -> UserRead:
    """
    Authorizes the user to access a resource based on their role hierarchy and scope.

    Args:
        user (UserRead): The authenticated user.
        operation_scopes (list[str], optional): The required scopes for the operation. Defaults to ["All"].
        operation_hierarchies (int, optional): The maximum role hierarchy level allowed for the operation. Defaults to 1.

    Raises:
        HTTPException: If the user does not have permission to access the resource.

    """

    print("Hierarchies: ", user.role.hierarchy)
    print("Scopes: ", user.scope.name)
    print("Check hier", user.role.hierarchy > operation_hierarchy_order)
    print(
        "Check scope",
        user.scope.name != DefaultScope.ALL and user.scope.name not in operation_scopes,
    )

    if (
        user.role.hierarchy != 1 and user.role.hierarchy > operation_hierarchy_order
    ) or (
        user.scope.name != DefaultScope.ALL.value
        and user.scope.name not in operation_scopes
    ):

        print("Raising exception...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to access this resource",
        )

    if custom_checks != None and not custom_checks:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to access this resource",
        )

    return user
