from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.users import UserRole


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    manager_id: int | None
    manager_name: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime


class PeoplePage(BaseModel):
    items: list[PersonOut]
    total: int
    limit: int
    offset: int
