from typing import Any, Literal, Union
import pytest
from sqlmodel import Session, col, select

from app.models.enterprise import Enterprise, EnterpriseRelation
from app.models.role import Role, RoleRelation
from app.models.scope import Scope, ScopeRelation
from app.models.user import User, UserRead


@pytest.fixture(scope="function")
def populate_data(db_session: Session) -> dict[str, Any]:
    session = db_session
    # Create default roles and scopes
    default_roles = ["Admin", "User"]
    default_scopes = ["HumanResource", "Stock", "Sales"]
    default_enterprise = Enterprise(
        name="Jarucucu",
        accountable_email="fulano@test.mail.com",
        activity_type="Fishing",
    )

    session.add(default_enterprise)
    session.commit()

    session.refresh(default_enterprise)

    for role_name in default_roles:
        role = Role(name=role_name, enterprise_id=default_enterprise.id, hierarchy=1)
        session.add(role)

    for scope_name in default_scopes:
        scope = Scope(name=scope_name, enterprise_id=default_enterprise.id)
        session.add(scope)

    session.commit()
    session.refresh(default_enterprise)

    # roles_query = select(Role).where(Role.enterprise_id == default_enterprise.id)

    roles_scopes_query = (
        select(Scope.id, Role.id)
        .where(Role.enterprise_id == default_enterprise.id)
        .join(Scope, col(Role.enterprise_id) == col(Scope.enterprise_id))
    )
    r_s_result = session.exec(
        roles_scopes_query
    ).all()  # , session.exec(scopes_query).all()
    roles_id = list(map(lambda x: x[0], r_s_result))
    scopes_id = list(map(lambda x: x[1], r_s_result))

    return {
        "enterprise": default_enterprise,
        "roles_id": roles_id,
        "scopes_id": scopes_id,
    }


@pytest.fixture(scope="function")
def create_default_user(db_session: Session, populate_data: dict[str, Any]):
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role_id=populate_data["roles_id"][0],
        scope_id=populate_data["scopes_id"][0],
        enterprise_id=populate_data["enterprise"].id,
    )
    db_session.add(user)
    db_session.commit()

    db_session.refresh(user)

    return {"user": user, **populate_data}


def test_create_user(
    db_session: Session,
    populate_data: Union[dict[Literal["enterprise"], Enterprise], dict[str, Any]],
):
    assert "roles_id" in populate_data
    assert isinstance(populate_data["roles_id"], list)

    assert "scopes_id" in populate_data
    assert isinstance(populate_data["scopes_id"], list)

    role_id: int = populate_data["roles_id"][0]
    scope_id: int = populate_data["scopes_id"][0]
    # Test creating a user
    user = User(
        id=None,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role_id=role_id,
        scope_id=scope_id,
        enterprise_id=populate_data["enterprise"].id,
    )
    db_session.add(user)
    db_session.commit()

    db_session.refresh(user)

    assert user.id is not None
    assert user.scope_id is not None
    assert user.scope_id == populate_data["scopes_id"][0]
    assert user.role_id is not None
    assert user.role_id == populate_data["roles_id"][0]
    assert user.enterprise is not None
    assert user.enterprise.name == populate_data["enterprise"].name
    assert user.scope is not None
    assert user.scope.name == "HumanResource"
    assert isinstance(user.id, int)


def test_read_user(create_default_user: dict[str, Any], db_session: Session):
    # Test reading a user
    result = db_session.exec(
        select(User).where(User.username == create_default_user["user"].username)
    ).first()

    assert result is not None
    assert result.id is not None
    assert isinstance(result.id, int)
    assert result.scope is not None
    assert result.scope.name == "HumanResource"
    assert result.username == "testuser"


def test_update_user(create_default_user: dict[str, Any], db_session: Session):
    # Test updating a user
    user = create_default_user["user"]

    assert user is not None

    user.full_name = "Updated Test User"
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    result = db_session.exec(select(User).where(User.id == user.id)).first()
    assert result is not None
    assert result.full_name == "Updated Test User"


def test_delete_user(populate_data: dict[str, Any], db_session: Session):
    assert "roles_id" in populate_data
    assert type(populate_data["roles_id"]) == list

    assert "scopes_id" in populate_data
    assert type(populate_data["scopes_id"]) == list

    role_id: int = populate_data["roles_id"][1]
    scope_id: int = populate_data["scopes_id"][1]

    # Test deleting a user
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role_id=role_id,
        scope_id=scope_id,
        enterprise_id=populate_data["enterprise"].id,
    )
    db_session.add(user)
    db_session.commit()

    result = db_session.exec(select(User).where(User.id == user.id)).first()
    assert result is not None
    assert result.id is not None
    assert len(result.username) > 0

    db_session.delete(user)
    db_session.commit()

    result = db_session.exec(select(User).where(User.id == user.id)).first()
    assert result is None


def test_query_scope_role_by_id(
    create_default_user: dict[str, Any], db_session: Session
):
    # Test querying a user by role and scope id
    with db_session as session:

        user = create_default_user["user"]
        roles = create_default_user["roles_id"]
        scopes = create_default_user["scopes_id"]

        user_read_params = User(
            username="testuser2",
            email="test2@example.com",
            full_name="Test User 2",
            role_id=roles[1],
            scope_id=scopes[2],
            enterprise_id=user.enterprise.id,
        )

        session.add(user_read_params)
        session.commit()
        session.refresh(user_read_params)

        assert user_read_params.role is not None
        assert user_read_params.scope is not None
        assert user_read_params.enterprise is not None

        user_read = UserRead(
            role=RoleRelation(**user_read_params.role.model_dump()),
            scope=ScopeRelation(**user_read_params.scope.model_dump()),
            enterprise=EnterpriseRelation(**user_read_params.enterprise.model_dump()),
            **user_read_params.model_dump()
        )

        result: tuple[Enterprise, Scope, Role] | None = None

        assert user is not None
        assert user_read_params is not None
        assert user.role_id is not None
        assert user.scope_id is not None
        assert user_read.query_scope_role_by_id(user.role_id, user.scope_id) is not None

        result = session.exec(
            user_read.query_scope_role_by_id(user.role_id, user.scope_id)
        ).first()

        assert result is not None

        _, scope, role = result
        assert result is not None
        assert scope.id == user.scope_id
        assert role.id == user.role_id
        assert scope.name == user.scope.name
        assert role.name == user.role.name
        assert role.hierarchy == user.role.hierarchy
