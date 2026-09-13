from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.limits import NAME_MAX, NAME_MIN, PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
from app.core.sorting import SortOrder
from app.models.users import UserRole

INVITABLE_ROLES = frozenset({UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR})


class PeopleSortField(StrEnum):
    NAME = "name"
    EMAIL = "email"
    ROLE = "role"
    CREATED_AT = "created_at"


class PeopleQuery(BaseModel):
    role: UserRole | None = None
    manager_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    limit: int = Field(default=PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX)
    offset: int = Field(default=0, ge=0)
    sort_by: PeopleSortField = PeopleSortField.NAME
    order: SortOrder = SortOrder.ASC


class InviteRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=NAME_MIN, max_length=NAME_MAX)
    last_name: str = Field(min_length=NAME_MIN, max_length=NAME_MAX)
    role: UserRole = UserRole.OPERATOR
    manager_id: int | None = Field(default=None, ge=1)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("role")
    @classmethod
    def check_role(cls, value: UserRole) -> UserRole:
        if value not in INVITABLE_ROLES:
            raise ValueError("role cannot be assigned by invitation")
        return value


class PersonUpdate(BaseModel):
    role: UserRole | None = None
    manager_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def check_role(cls, value: UserRole | None) -> UserRole | None:
        if value is not None and value not in INVITABLE_ROLES:
            raise ValueError("role cannot be assigned here")
        return value
