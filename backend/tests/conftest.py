from typing import Any

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session

from app.db.conn import get_db
from app.main import app
from app.middlewares.auth import authenticate_user
from app.middlewares.send_message import get_async_message_sender_on_loop
from app.models.enterprise import Enterprise, EnterpriseRelation
from app.models.role import DefaultRole, DefaultRoleSchema, Role, RoleRelation
from app.models.scope import DefaultScope, DefaultScopeSchema, Scope, ScopeRelation
from app.models.user import User, UserRead

# SQLite database URL for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create a SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create a sessionmaker to manage sessions
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the database
SQLModel.metadata.create_all(bind=engine)


@asynccontextmanager
async def override_lifespan(fapi_app: FastAPI, *args, **kwargs):
    # pylint: disable=unused-argument

    print("Span")
    yield


async def test_sender_on_loop(message: str):
    # pylint: disable=unused-argument

    pass


def override_get_async_message_sender_on_loop():
    return test_sender_on_loop


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session with a rollback at the end of the test."""

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autocommit=False, autoflush=False)

    try:
        yield session
        print("Closing session...............")
    finally:
        if session.is_active:
            session.close()
        transaction.rollback()
        connection.close()


def get_test_client_authenticated(user: UserRead):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autocommit=False, autoflush=False)

    def override_get_session():
        yield session

    def override_authenticate_user(token: str = "") -> Any:
        # pylint: disable=unused-argument

        user_dict = user.model_dump()
        user_dict.pop("hashed_password", "")
        return UserRead(**user_dict)

    app.dependency_overrides[get_async_message_sender_on_loop] = (
        override_get_async_message_sender_on_loop
    )
    app.dependency_overrides[get_db] = override_get_session
    app.dependency_overrides[authenticate_user] = override_authenticate_user
    app.router.lifespan_context = override_lifespan

    yield (session, connection, transaction, TestClient(app))


@pytest.fixture(scope="function")
def test_client(db_session: Session):
    # pylint: disable=redefined-outer-name
    """Create a test client that uses the override_get_db fixture to return a session."""

    def override_get_session():
        # try:
        yield db_session
        # finally:
        #     db_session.close()

    app.dependency_overrides[get_db] = override_get_session
    app.router.lifespan_context = override_lifespan
    app.dependency_overrides[get_async_message_sender_on_loop] = (
        override_get_async_message_sender_on_loop
    )

    with TestClient(app) as test_client_override:
        yield test_client_override


@pytest.fixture(scope="function")
def enterprise_role_scope(db_session: Session) -> dict[str, Any]:
    # pylint: disable=redefined-outer-name

    session = db_session

    # Create default roles and scopes
    default_roles = DefaultRoleSchema.get_default_roles()
    default_scopes = DefaultScopeSchema.get_default_scopes()
    default_enterprise = Enterprise(
        id=None,
        name="Jarucucu",
        accountable_email="fulano@test.mail.com",
        activity_type="Fishing",
    )

    for roleschema in default_roles.values():
        role = Role(**roleschema)
        if default_enterprise.roles is not None:
            default_enterprise.roles.append(role)
        else:
            default_enterprise.roles = [role]

    for scopeschema in default_scopes.values():
        scope = Scope(**scopeschema)
        if default_enterprise.scopes is not None:
            default_enterprise.scopes.append(scope)
        else:
            default_enterprise.scopes = [scope]

    session.add(default_enterprise)
    session.commit()
    session.refresh(default_enterprise)

    print("###############################################")
    print("Created defaults: ", str(default_enterprise.model_dump()))

    return {
        "enterprise": default_enterprise,
        "roles": default_enterprise.roles,
        "scopes": default_enterprise.scopes,
    }


@pytest.fixture(scope="function")
def create_default_user(db_session: Session, enterprise_role_scope: dict[str, Any]):
    # pylint: disable=redefined-outer-name

    roles: list[Role] = enterprise_role_scope["roles"]
    role = list(filter(lambda role: role.name == DefaultRole.OWNER.value, roles))[0]

    scopes: list[Scope] = enterprise_role_scope["scopes"]
    scope = list(filter(lambda scope: scope.name == DefaultScope.ALL.value, scopes))[0]

    user = User(
        id=None,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role_id=role.id,
        scope_id=scope.id,
        enterprise_id=enterprise_role_scope["enterprise"].id,
    )
    db_session.add(user)
    db_session.commit()

    db_session.refresh(user)

    return {"user": user, **enterprise_role_scope}


@pytest.fixture(scope="function")
def test_client_authenticated_default(
    db_session: Session, create_default_user: dict[str, Any]
):
    # pylint: disable=redefined-outer-name

    user: User = create_default_user["user"]
    role: Role = list(
        filter(lambda role: role.id == user.role_id, create_default_user["roles"])
    )[0]
    scope: Scope = list(
        filter(lambda scope: scope.id == user.scope_id, create_default_user["scopes"])
    )[0]
    enterprise: Enterprise = create_default_user["user"].enterprise

    user_dict = user.model_dump()
    user_dict.pop("hashed_password", "")

    print("###############################################")
    print(str(user_dict))
    print(str(enterprise.model_dump()))
    print(str(role.model_dump()))
    print(str(scope.model_dump()))

    user_read = UserRead(
        **user_dict,
        role=RoleRelation(**role.model_dump()),
        scope=ScopeRelation(**scope.model_dump()),
        enterprise=EnterpriseRelation(**enterprise.model_dump())
    )

    def override_get_session():
        # try:
        yield db_session
        # finally:
        #     db_session.close()

    def override_authenticate_user(token: str = "") -> Any:
        # pylint: disable=unused-argument

        return user_read

    app.dependency_overrides[get_db] = override_get_session
    app.dependency_overrides[authenticate_user] = override_authenticate_user
    app.dependency_overrides[get_async_message_sender_on_loop] = (
        override_get_async_message_sender_on_loop
    )
    app.router.lifespan_context = override_lifespan

    test_client = TestClient(app)
    # try:
    return test_client
    # except:
    #     if test_client is not None and not test_client.is_closed:
    #         test_client.close()
    # finally:
    #     if test_client is not None and not test_client.is_closed:
    #         test_client.close()


@pytest.fixture(scope="function")
def test_client_auth_default_with_broker(test_client_authenticated_default: TestClient):
    # pylint: disable=redefined-outer-name

    my_app = test_client_authenticated_default.app

    if isinstance(my_app, FastAPI):
        my_app.dependency_overrides[get_async_message_sender_on_loop] = (
            get_async_message_sender_on_loop
        )

    test_client_authenticated_default.app = my_app

    return test_client_authenticated_default
