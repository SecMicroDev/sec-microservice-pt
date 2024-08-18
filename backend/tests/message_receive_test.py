from collections.abc import Generator
import datetime
import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
import itertools
from sqlalchemy.engine import Engine
from app.messages.event import UpdateEvent
from app.models.enterprise import (
    Enterprise,
    EnterpriseRelation,
    EnterpriseWithHierarchy,
)
from app.models.role import DefaultRole, Role, RoleRelation
from app.models.scope import DefaultScope, Scope, ScopeRelation
from app.models.user import User, UserRead
from sqlmodel import SQLModel, Session, StaticPool, create_engine, select

from app.router.utils import (
    EnterpriseCreateEvent,
    EnterpriseDeleteEvent,
    EnterpriseDeleteWithId,
    EnterpriseUpdateEvent,
    EnterpriseUpdateWithId,
    UserCreateEvent,
    UserDeleteEvent,
    UserDeleteWithId,
    UserUpdateEvent,
    UserUpdateWithId,
)


@pytest.fixture(scope="function")
def setup_db() -> Engine:
    # SQLite database URL for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

    # Create a SQLAlchemy engine
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables in the database
    SQLModel.metadata.create_all(bind=engine)
    return engine


def setup_db_defaults(local_db_session: Session) -> tuple[User, Enterprise]:
    enterprise = Enterprise(
        id=None, name="TestEnterprise", accountable_email="testenterprise@test.mail.com"
    )

    local_db_session.add(enterprise)
    local_db_session.commit()
    local_db_session.refresh(enterprise)

    assert enterprise.id is not None

    role = Role(
        id=None,
        name=DefaultRole.OWNER.value,
        description="Test Role Description",
        hierarchy=DefaultRole.get_default_hierarchy(DefaultRole.OWNER.value),
        enterprise_id=enterprise.id,
    )

    scope = Scope(
        id=1,
        name=DefaultScope.SELLS.value,
        description="Test Role Description",
        enterprise_id=enterprise.id,
    )

    scope_all = Scope(
        id=2,
        name=DefaultScope.ALL.value,
        description="Test Role Description",
        enterprise_id=enterprise.id,
    )

    enterprise.roles = [
        role,
        Role(
            id=None,
            name=DefaultRole.MANAGER.value,
            description="Test Manager Description",
            hierarchy=DefaultRole.get_default_hierarchy(DefaultRole.MANAGER.value),
            enterprise_id=enterprise.id,
        ),
        Role(
            id=None,
            name=DefaultRole.COLLABORATOR.value,
            description="Test Collaborator Description",
            hierarchy=DefaultRole.get_default_hierarchy(DefaultRole.COLLABORATOR.value),
            enterprise_id=enterprise.id,
        ),
    ]

    enterprise.scopes = [
        scope,
        scope_all,
        Scope(
            id=None,
            name=DefaultScope.PATRIMONIAL.value,
            description="Test Role Description",
            enterprise_id=enterprise.id,
        ),
        Scope(
            id=None,
            name=DefaultScope.HUMAN_RESOURCE.value,
            description="Test Role Description",
            enterprise_id=enterprise.id,
        ),
    ]

    local_db_session.add(enterprise)
    local_db_session.commit()
    local_db_session.refresh(enterprise)

    saved_user = User(
        id=None,
        username="testuser",
        email="testemail@test.mail.com",
        full_name="Test User",
        role_id=enterprise.roles[0].id,
        scope_id=enterprise.scopes[2].id,
        enterprise_id=enterprise.id,
    )

    saved_user.role = enterprise.roles[0]
    saved_user.scope = enterprise.scopes[2]

    enterprise.users = [saved_user]

    local_db_session.add(enterprise)
    local_db_session.commit()
    local_db_session.refresh(saved_user)
    local_db_session.refresh(enterprise)

    return (saved_user, enterprise)


def gen_db(session: Session) -> Generator:
    yield session


id_counter = itertools.count(start=11, step=1)


def get_id() -> int:
    for i in id_counter:
        return i

    return 11


def map_enterprise_roles_scope(r: Role | Scope):
    r.id = get_id()
    r.enterprise_id = r.enterprise_id + 1
    return r


def map_enterprise_relation(e: Enterprise):
    return EnterpriseRelation(**e.model_dump())


def map_role_relation(r: Role):
    return RoleRelation(**r.model_dump())


def map_scope_relation(s: Scope):
    return ScopeRelation(**s.model_dump())


@pytest.mark.asyncio
@patch("app.messages.event.get_db")
async def test_create_user_event(mock_get: Mock, setup_db: Engine):
    connection = setup_db.connect()
    transaction = connection.begin()
    local_db_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    with local_db_session:

        mock_get.return_value = gen_db(local_db_session)

        message_dict: dict[str, Any] = {
            **json.loads(
                UserCreateEvent(
                    event_scope=DefaultScope.ALL.value,
                    data=UserRead(
                        id=5,
                        username="testuser2",
                        email="testemail2@test.mail.com",
                        full_name="Test User 2",
                        role=RoleRelation(
                            id=1, name=DefaultRole.OWNER.value, hierarchy=1
                        ),
                        scope=ScopeRelation(id=1, name=DefaultScope.ALL.value),
                        enterprise=EnterpriseRelation(
                            id=1,
                            name="TestEnterprise",
                            accountable_email="testenterprisemail@test.com",
                        ),
                        created_at=datetime.datetime.now(),
                    ),
                ).model_dump_json()
            ),
            "start_date": datetime.datetime.now().isoformat(),
            "origin": "rh_service",
        }

        # Arrange
        message = json.dumps(message_dict)

        # Act
        await UpdateEvent.process_message(message)

        mock_get.assert_called_once()

        # Assert
        user = local_db_session.exec(
            select(User).where(User.username == "testuser2")
        ).first()

        with local_db_session:
            assert user is not None
            assert user.username == "testuser2"
            assert user.email == "testemail2@test.mail.com"
            assert user.full_name == "Test User 2"
            assert user.role_id == message_dict["data"]["role"]["id"]
            assert user.scope_id == message_dict["data"]["scope"]["id"]
            assert user.enterprise_id == message_dict["data"]["enterprise"]["id"]

    transaction.rollback()

    if local_db_session.is_active:
        local_db_session.close()

    connection.close()


@pytest.mark.asyncio
@patch("app.messages.event.get_db")
async def test_update_user_event(mock_get: Mock, setup_db: Engine):
    connection = setup_db.connect()
    transaction = connection.begin()
    local_db_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    mock_get.return_value = gen_db(local_db_session)

    saved_user, enterprise = setup_db_defaults(local_db_session)

    assert saved_user is not None
    assert enterprise is not None and enterprise.scopes is not None
    assert saved_user.id is not None
    assert saved_user.enterprise_id is not None
    assert saved_user.role is not None and saved_user.scope is not None
    assert saved_user.role.name is not None
    assert saved_user.role.hierarchy is not None
    assert saved_user.scope.name is not None
    assert saved_user.enterprise is not None
    assert saved_user.enterprise.name is not None

    # Arrange
    message_dict: dict[str, Any] = {
        **json.loads(
            UserUpdateEvent(
                event_scope=DefaultScope.SELLS.value,
                update_scope=DefaultScope.PATRIMONIAL.value,
                user=UserRead(
                    **saved_user.model_dump(),
                    role=RoleRelation(
                        id=saved_user.role.id,
                        name=saved_user.role.name,
                        hierarchy=saved_user.role.hierarchy,
                    ),
                    scope=ScopeRelation(
                        id=enterprise.scopes[0].id,
                        name=enterprise.scopes[0].name,
                    ),
                    enterprise=EnterpriseRelation(
                        id=saved_user.enterprise_id,
                        name=saved_user.enterprise.name,
                        accountable_email=enterprise.accountable_email,
                    )
                ),
                data=UserUpdateWithId(
                    id=saved_user.id,
                    enterprise_id=saved_user.enterprise_id,
                    username="updateduser",
                    email="updatedemail@test.mail.com",
                    scope_id=enterprise.scopes[2].id,
                ),
            ).model_dump_json()
        ),
        "start_date": datetime.datetime.now().isoformat(),
        "origin": "rh_service",
    }

    message = json.dumps(message_dict)

    local_db_session.close()

    # Act
    await UpdateEvent.process_message(message)

    mock_get.assert_called_once()

    # Assert
    new_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    with new_session:
        user = new_session.exec(select(User).where(User.id == saved_user.id)).first()
        assert user is not None
        assert user.username == "updateduser"
        assert user.email == "updatedemail@test.mail.com"
        assert user.scope_id == message_dict["data"]["scope_id"]
        assert user.enterprise_id == message_dict["data"]["enterprise_id"]

    transaction.rollback()

    if new_session.is_active:
        new_session.close()

    if local_db_session.is_active:
        local_db_session.close()

    connection.close()


@pytest.mark.asyncio
@patch("app.messages.event.get_db")
async def test_delete_user_event(mock_get: Mock, setup_db: Engine):
    connection = setup_db.connect()
    transaction = connection.begin()
    local_db_session = Session(autocommit=False, autoflush=False, bind=setup_db)
    saved_user, _ = setup_db_defaults(local_db_session)

    assert saved_user is not None
    assert saved_user.id is not None

    mock_get.return_value = gen_db(local_db_session)

    assert saved_user.enterprise_id

    message_dict = {
        **json.loads(
            UserDeleteEvent(
                event_scope=DefaultScope.PATRIMONIAL.value,
                data=UserDeleteWithId(
                    id=saved_user.id,
                    enterprise_id=saved_user.enterprise_id,
                ),
            ).model_dump_json()
        ),
        "start_date": datetime.datetime.now().isoformat(),
        "origin": "rh_service",
    }

    message = json.dumps(message_dict)

    local_db_session.close()

    # Act
    await UpdateEvent.process_message(message)

    mock_get.assert_called_once()

    # Assert
    new_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    with new_session:
        user = new_session.get(User, saved_user.id)
        assert user is None

    transaction.rollback()

    if new_session.is_active:
        new_session.close()

    if local_db_session.is_active:
        local_db_session.close()

    connection.close()


@pytest.mark.asyncio
@patch("app.messages.event.get_db")
async def test_create_enterprise_event(mock_get: Mock, setup_db: Engine):
    transaction = setup_db.connect()
    local_db_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    saved_user, enterprise = setup_db_defaults(local_db_session)

    mock_get.return_value = gen_db(local_db_session)

    assert saved_user.id is not None
    assert enterprise.id is not None
    assert enterprise.roles is not None
    assert enterprise.scopes is not None

    new_roles = [
        Role(
            id=get_id(),
            name="Test Role",
            description="New Test Role Description",
            hierarchy=2,
            enterprise_id=enterprise.id + 1,
        ),
        *map(map_enterprise_roles_scope, enterprise.roles),
    ]

    new_scopes = [
        Scope(
            id=get_id(),
            name="Test Scope",
            description="New Test Scope Description",
            enterprise_id=enterprise.id + 1,
        ),
        *map(map_enterprise_roles_scope, enterprise.scopes),
    ]

    message_dict = {
        **json.loads(
            EnterpriseCreateEvent(
                event_scope=DefaultScope.ALL.value,
                data=EnterpriseWithHierarchy(
                    id=enterprise.id + 1,
                    name="NewEnterprise",
                    accountable_email="newenterprise@test.mail.com",
                    roles=list(map(map_role_relation, new_roles)),
                    scopes=list(map(map_scope_relation, new_scopes)),
                ),
            ).model_dump_json()
        ),
        "start_date": datetime.datetime.now().isoformat(),
        "origin": "rh_service",
    }

    # Arrange
    message = json.dumps(message_dict)

    local_db_session.close()

    # Act
    await UpdateEvent.process_message(message)

    mock_get.assert_called_once()

    # Assert
    new_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    with new_session:
        enterprise = new_session.exec(
            select(Enterprise).where(Enterprise.name == "NewEnterprise")
        ).first()

        assert enterprise is not None
        assert enterprise.name == "NewEnterprise"
        assert enterprise.accountable_email == "newenterprise@test.mail.com"

    transaction.rollback()

    if new_session.is_active:
        new_session.close()

    if local_db_session.is_active:
        local_db_session.close()


@pytest.mark.asyncio
@patch("app.messages.event.get_db")
async def test_update_enterprise_event(mock_get: Mock, setup_db: Engine):
    connection = setup_db.connect()
    transaction = connection.begin()
    local_db_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    mock_get.return_value = gen_db(local_db_session)

    saved_user, enterprise = setup_db_defaults(local_db_session)

    assert saved_user.id is not None
    assert enterprise.id is not None

    message_dict = {
        **json.loads(
            EnterpriseUpdateEvent(
                event_scope=DefaultScope.ALL.value,
                data=EnterpriseUpdateWithId(
                    id=enterprise.id,
                    name="UpdatedEnterprise",
                    accountable_email="updatedenterprise@test.mail.com",
                ),
            ).model_dump_json(exclude_none=True)
        ),
        "start_date": datetime.datetime.now().isoformat(),
        "origin": "rh_service",
    }

    # Arrange
    message = json.dumps(message_dict)

    local_db_session.close()

    # Act
    await UpdateEvent.process_message(message)

    mock_get.assert_called_once()

    # Assert
    # local_db_session.close()

    new_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    with new_session:
        updated_enterprise = new_session.exec(
            select(Enterprise).where(Enterprise.id == enterprise.id)
        ).first()
        assert updated_enterprise is not None
        assert updated_enterprise.name == "UpdatedEnterprise"
        assert updated_enterprise.accountable_email == "updatedenterprise@test.mail.com"

    transaction.rollback()
    connection.rollback()

    if new_session.is_active:
        new_session.close()

    if local_db_session.is_active:
        local_db_session.close()

    connection.close()


@pytest.mark.asyncio
@patch("app.messages.event.get_db")
async def test_delete_enterprise_event(mock_get: Mock, setup_db: Engine):
    transaction = setup_db.connect()
    local_db_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    saved_user, enterprise = setup_db_defaults(local_db_session)

    mock_get.return_value = gen_db(local_db_session)

    assert saved_user.id is not None
    assert enterprise.id is not None

    message_dict = {
        **json.loads(
            EnterpriseDeleteEvent(
                event_scope=DefaultScope.ALL.value,
                data=EnterpriseDeleteWithId(id=enterprise.id),
            ).model_dump_json()
        ),
        "start_date": datetime.datetime.now().isoformat(),
        "origin": "rh_service",
    }

    # Arrange
    message = json.dumps(message_dict)

    local_db_session.close()

    # Act
    await UpdateEvent.process_message(message)

    mock_get.assert_called_once()

    # Assert
    new_session = Session(autocommit=False, autoflush=False, bind=setup_db)

    with new_session:
        deleted_enterprise = new_session.exec(
            select(Enterprise).where(Enterprise.id == enterprise.id)
        ).first()
        assert deleted_enterprise is None

    transaction.rollback()

    if new_session.is_active:
        new_session.close()

    if local_db_session.is_active:
        local_db_session.close()
