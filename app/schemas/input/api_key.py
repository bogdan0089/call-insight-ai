from pydantic import BaseModel, Field, field_validator

from app.core.limits import API_KEY_NAME_MAX


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=API_KEY_NAME_MAX)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned
