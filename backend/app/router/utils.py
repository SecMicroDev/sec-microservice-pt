from enum import Enum
from sqlmodel import SQLModel
from app.models.enterprise import EnterpriseUpdate, EnterpriseWithHierarchy
from app.models.scope import DefaultScope
from app.models.user import UserRead, UserUpdate


class UserEvents(str, Enum):
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_LOGIN = "USER_LOGIN"


class EnterpriseEvents(str, Enum):
    ENTERPRISE_CREATED = "ENTERPRISE_CREATED"
    ENTERPRISE_UPDATED = "ENTERPRISE_UPDATED"
    ENTERPRISE_DELETED = "ENTERPRISE_DELETED"


class BaseEventMessage(SQLModel):
    event: str
    event_scope: str = DefaultScope.ALL.value 


class BaseUserEventMessage(BaseEventMessage):
    event_scope: str = DefaultScope.ALL.value 


class UserCreateEvent(BaseUserEventMessage):
    event: str = UserEvents.USER_CREATED.value
    data: UserRead


class UserUpdateWithId(UserUpdate):
    id: int
    enterprise_id: int


class UserDeleteWithId(SQLModel):
    id: int
    enterprise_id: int


class UserUpdateEvent(BaseUserEventMessage):
    event: str = UserEvents.USER_UPDATED.value
    update_scope: str = DefaultScope.ALL.value
    user: UserRead
    data: UserUpdateWithId


class UserDeleteEvent(BaseUserEventMessage):
    event: str = UserEvents.USER_DELETED.value
    data: UserDeleteWithId


class EnterpriseCreateEvent(BaseEventMessage):
    event: str = EnterpriseEvents.ENTERPRISE_CREATED.value
    data: EnterpriseWithHierarchy


class EnterpriseUpdateWithId(EnterpriseUpdate):
    id: int


class EnterpriseUpdateEvent(BaseEventMessage):
    event: str = EnterpriseEvents.ENTERPRISE_UPDATED.value
    data: EnterpriseUpdateWithId


class EnterpriseDeleteWithId(SQLModel):
    id: int


class EnterpriseDeleteEvent(BaseEventMessage):
    event: str = EnterpriseEvents.ENTERPRISE_DELETED.value
    data: EnterpriseDeleteWithId
