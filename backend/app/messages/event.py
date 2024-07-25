import asyncio
from collections.abc import Callable
import datetime
import json
from sys import stdout
from typing import Any


from app.router.utils import EnterpriseEvents, UserEvents
from sqlmodel import Session, select

from app.db.conn import get_db
from app.models.enterprise import Enterprise, EnterpriseUpdate
from app.models.user import User, UserRead
from app.models.role import BaseRole, Role
from app.models.scope import BaseScope, DefaultScope, Scope


class UpdateEvent:
    def __init__(
        self,
        event: str,
        event_scope: str,
        data: dict[str, Any],
        start_date: datetime.datetime,
        origin: str,
        update_scope: str | None = None,
        full_user: dict[str, Any] | None = None,
    ):

        self.event = event
        self.event_scope = event_scope
        self.data = data
        self.start_date = start_date
        self.origin = origin
        self.update_scope = update_scope
        self.full_user = full_user

    @classmethod
    def create_from_message(cls, message: str) -> "UpdateEvent | None":
        message_dict = {}
        try:
            message_dict = json.loads(message)
        except json.JSONDecodeError:
            print("Error: Failed to decode message")
            print("Invalid Message: ", message)
            return None

        if any(
            map(
                lambda x: x not in message_dict,
                ("event", "event_scope", "data", "origin", "start_date"),
            )
        ):
            print("Error: RECEIVED INVALID MESSAGE")
            print("Invalid Message: ", message)
            return None

        return cls(
            message_dict["event"],
            message_dict["event_scope"],
            message_dict["data"],
            datetime.datetime.fromisoformat(message_dict["start_date"]),
            message_dict["origin"],
            update_scope=message_dict.get("update_scope", None),
            full_user=message_dict.get("user", None),
        )

    @classmethod
    async def process_message(cls, message: str):
        print("Creating message processor...")
        print(f"Received message: {message}")
        event = cls.create_from_message(message)
        if event is not None:
            print("Created event. Updating database...")
            await event.update_table()
        else:
            print("Error: Event is NONE")

        stdout.flush()

    def _check_valid_user_event(self):
        user_events = (
            UserEvents.USER_CREATED,
            UserEvents.USER_UPDATED,
            UserEvents.USER_DELETED,
        )
        enterprise_events = (
            EnterpriseEvents.ENTERPRISE_CREATED,
            EnterpriseEvents.ENTERPRISE_UPDATED,
            EnterpriseEvents.ENTERPRISE_DELETED,
        )

        if self.event in (user_events + enterprise_events):
            check_update_scope = ""
            check_update_scope = (
                self.update_scope if self.update_scope is not None else ""
            )
            check_resp = any(
                (
                    self.event_scope == DefaultScope.PATRIMONIAL.value,
                    self.event_scope == DefaultScope.ALL.value,
                    check_update_scope == DefaultScope.PATRIMONIAL.value,
                    check_update_scope == DefaultScope.ALL.value,
                )
            )

            print(f"Valid event for PT: {check_resp}")
            return check_resp

        print("Ignoring event for PT.")
        stdout.flush()
        return False

    async def __db_access_loop(self, db_function_callback: Callable, retries: int = 5):
        db: Session | None = None
        err: Exception | None = None
        counter = retries
        print(f"Start enterprise update: Data -- {self.data}")
        while counter > 0:
            try:
                db = next(get_db())
                if db is None:
                    print("No database connection")
                    print("Waiting for 5 seconds...")
                    await asyncio.sleep(5)
                    counter -= 1
                    continue

                db_function_callback(db)

                if db.is_active:
                    db.close()

                break

            except Exception as e:
                print("Messaging error: ", e.__str__())
                err = e
                if db:
                    db.rollback()
                    if db.is_active:
                        db.close()
                    await asyncio.sleep(5)
                    counter -= 1
                    continue

        if counter == 0:
            print("Failed to update the database")
            print("Data: ", self.data)
            if db is None:
                print("No database connection")
                stdout.flush()
                raise Exception("Failed to connect to the database")
            if err:
                print(f"Error {err.__str__()}: ", err)
                stdout.flush()
                raise err

        stdout.flush()

    async def update_table(self):
        if not self._check_valid_user_event():
            return

        if self.event == EnterpriseEvents.ENTERPRISE_CREATED:
            print("Received CreateEnterprise event")
            await self.create_enterprise()
        elif self.event == EnterpriseEvents.ENTERPRISE_UPDATED:
            print("Received UpdateEnterpise event")
            await self.update_enterprise()
        elif self.event == EnterpriseEvents.ENTERPRISE_DELETED:
            print("Received DeleteEnterprise event")
            await self.delete_enterprise()

        elif self.event == UserEvents.USER_CREATED:
            print("Received CreateUser event")
            await self.create_user()
        elif self.event == UserEvents.USER_DELETED:
            print("Received DeleteUser event")
            await self.delete_user()
        elif self.event == UserEvents.USER_UPDATED:
            print("Received UpdateUser event")
            await self.update_user()

        stdout.flush()

    async def update_enterprise(self):
        def db_access(db: Session):
            try:
                print(f"Start Enterprise update: Data -- {self.data}")
                with db as session:
                    enterprise_update = EnterpriseUpdate(**self.data)
                    enterprise = session.get(Enterprise, self.data["id"])

                    if enterprise is not None:

                        for key, value in enterprise_update.model_dump(
                            exclude_none=True
                        ).items():
                            if hasattr(enterprise, key):
                                print(f"Setting {key} to {value}")
                                setattr(enterprise, key, value)

                        print("Updating enterprise...")
                        session.add(enterprise)
                        session.commit()

                    else:
                        print(f'Enterprise with id {self.data["id"]} not found')

                stdout.flush()
            except Exception as e:
                print(
                    f'Failed to update enterprise {self.data["name"]} - ID: {self.data["id"]} on DB'
                )
                print(f"Error: {e}")

        await self.__db_access_loop(db_access)

    async def update_user(self):
        def db_access(db: Session):

            name = ""
            id = 0

            try:
                role: Role | None = None
                scope: Scope | None = None

                print(f"Start User update: Data -- {self.data}")

                if (
                    self.full_user is not None
                    and self.data.get("enterprise_id")
                    and self.data.get("id")
                ):

                    with db as session:
                        print("Interacting with the database...")

                        user_read = UserRead(**self.full_user)
                        db_user = session.get(User, self.data["id"])

                        if db_user is not None:
                            name = db_user.username
                            id = db_user.id

                            print(f"Found User {name} - ID {id}")

                            if (
                                user_read.scope.name != DefaultScope.ALL.value
                                and user_read.scope.name != DefaultScope.SELLS.value
                            ):

                                print(
                                    f"Deleting User: {user_read.username} -- ID {user_read.id}"
                                )
                                session.delete(db_user)
                                session.commit()
                                return

                            if self.data["role_id"]:
                                role = session.get(Role, self.data["role_id"])
                            elif "role_name" in self.data:
                                role = session.exec(
                                    BaseRole.get_roles_by_names(
                                        self.data["enterprise_id"],
                                        [self.data["role_name"]],
                                    )
                                ).first()

                                if "scope_id" in self.data:
                                    scope = session.get(Scope, self.data["scope_id"])
                                elif "scope_name" in self.data:
                                    scope = session.exec(
                                        BaseScope.get_roles_by_names(
                                            self.data["enterprise_id"],
                                            [self.data["scope_name"]],
                                        )
                                    ).first()

                                print("finding user...")

                            if role is not None:
                                print("Change role")
                                db_user.role_id = role.id
                                db_user.role = role

                            if scope is not None:
                                print("Change scope")
                                db_user.scope_id = scope.id
                                db_user.scope = scope

                            if "username" in self.data:
                                print("Updating Username")
                                db_user.username = self.data["username"]

                            if "email" in self.data:
                                print("Updating email")
                                db_user.email = self.data["email"]

                            if "full_name" in self.data:
                                print("Updating full_name")
                                db_user.full_name = self.data["full_name"]

                            print("Updating user on DB...")

                            session.add(db_user)
                            session.commit()

                            ################## VERIFYING SAVED USER ############
                            user_v = session.get(User, self.data["id"])
                            assert user_v is not None
                            print(f"User updated: {user_v.model_dump()}")

                        else:
                            print(f'User with id {self.data["id"]} not found')
                            if (
                                user_read.scope.name == DefaultScope.ALL.value
                                or user_read.scope.name == DefaultScope.SELLS.value
                            ):

                                session.add(User(**user_read.model_dump()))
                                session.commit()
            except Exception as e:
                print(f"Failed to update user {name} - ID: {id} on DB")
                print(f"Error: {e}")

        await self.__db_access_loop(db_access)

    async def create_enterprise(self):
        def db_access(db: Session):
            print(f"Start Enterprise creation: Data -- {self.data}")
            enterprise_name = self.data.get("name", None)
            enterprise_id = self.data.get("id", None)
            try:
                with db as session:
                    copy_data = self.data.copy()
                    roles = list(map(lambda r: Role(**r), copy_data.pop("roles")))
                    scopes = list(map(lambda s: Scope(**s), copy_data.pop("scopes")))

                    enterprise = Enterprise(**copy_data)
                    enterprise.roles = roles
                    enterprise.scopes = scopes

                    print("Creating enterprise...")
                    session.add(enterprise)
                    session.commit()

                stdout.flush()

            except Exception as e:
                print(
                    f"Failed to update user {enterprise_name} - ID: {enterprise_id} on DB"
                )
                print(f"Error: {e}")

        await self.__db_access_loop(db_access)

    async def delete_enterprise(self):
        def db_access(db: Session):
            print(f"Start Enterprise deletion: Data -- {self.data}")
            with db as session:
                enterprise = session.get(Enterprise, self.data["id"])
                if enterprise is not None:
                    print("Deleting enterprise...")
                    session.delete(enterprise)
                    session.commit()
                else:
                    print(f'Enterprise with id {self.data["id"]} not found')

        await self.__db_access_loop(db_access)

    async def create_user(self):
        def db_access(db: Session):
            try:
                print(f"Start User creation: Data -- {self.data}")
                read_data = self.data.copy()
                role = Role(**read_data.pop("role"))
                scope = Scope(**read_data.pop("scope"))
                enterprise = Enterprise(**read_data.pop("enterprise"))
                date_created = read_data.get("created_at", None)

                with db as session:
                    user = User(**read_data)
                    user.role_id = role.id
                    user.scope_id = scope.id
                    user.enterprise_id = enterprise.id
                    user.created_at = (
                        datetime.datetime.fromisoformat(date_created)
                        if date_created is not None
                        else datetime.datetime.now()
                    )
                    session.add(user)

                    session.commit()

            except Exception as e:
                print("Failed to create user")
                print(f"Error: {e}")

        await self.__db_access_loop(db_access)

    async def delete_user(self):
        def db_access(db: Session):
            print(f"Start User deletion: Data -- {self.data}")
            with db as session:
                user = session.get(User, self.data["id"])
                if user is not None:
                    print("Deleting user...")
                    session.delete(user)
                    session.commit()
                else:
                    print(f'User with id {self.data["id"]} not found')

        await self.__db_access_loop(db_access)
