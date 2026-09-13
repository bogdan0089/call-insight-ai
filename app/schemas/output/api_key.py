from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prefix: str
    is_active: bool
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyCreated(BaseModel):
    key: ApiKeyOut
    secret: str
    warning: str = "Ключ показується один раз — збережіть його зараз"
