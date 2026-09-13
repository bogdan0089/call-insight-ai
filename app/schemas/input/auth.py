import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.limits import (
    NAME_MAX,
    NAME_MIN,
    ORG_NAME_MAX,
    ORG_NAME_MIN,
    PASSWORD_MAX,
    PASSWORD_MIN,
    VERIFICATION_TOKEN_MAX,
    VERIFICATION_TOKEN_MIN,
)

PASSWORD_RULE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
    first_name: str = Field(min_length=NAME_MIN, max_length=NAME_MAX)
    last_name: str = Field(min_length=NAME_MIN, max_length=NAME_MAX)
    organization_name: str = Field(min_length=ORG_NAME_MIN, max_length=ORG_NAME_MAX)

    @field_validator("password")
    @classmethod
    def check_strength(cls, value: str) -> str:
        if not PASSWORD_RULE.match(value):
            raise ValueError("password must contain a letter and a digit")
        return value

    @field_validator("first_name", "last_name", "organization_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


class VerifyRequest(BaseModel):
    token: str = Field(
        min_length=VERIFICATION_TOKEN_MIN, max_length=VERIFICATION_TOKEN_MAX
    )


class ResendRequest(BaseModel):
    email: EmailStr


class AcceptInviteRequest(BaseModel):
    token: str = Field(
        min_length=VERIFICATION_TOKEN_MIN, max_length=VERIFICATION_TOKEN_MAX
    )
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)

    @field_validator("password")
    @classmethod
    def check_strength(cls, value: str) -> str:
        if not PASSWORD_RULE.match(value):
            raise ValueError("password must contain a letter and a digit")
        return value
