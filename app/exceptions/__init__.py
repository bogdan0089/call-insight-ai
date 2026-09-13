from app.exceptions.app_exception import AppException
from app.exceptions.auth_exceptions import (
    AccountDisabled,
    EmailNotVerified,
    InvalidCredentials,
    InvalidVerificationToken,
    NotAuthenticated,
    PermissionDenied,
)
from app.exceptions.db_exceptions import (
    AlreadyExistsError,
    ConstraintViolationError,
    DatabaseError,
    EntityNotFound,
    ForeignKeyViolationError,
)
from app.exceptions.rate_limit_exceptions import RateLimitUnavailable, TooManyRequests

__all__ = [
    "AccountDisabled",
    "AlreadyExistsError",
    "AppException",
    "ConstraintViolationError",
    "DatabaseError",
    "EmailNotVerified",
    "EntityNotFound",
    "ForeignKeyViolationError",
    "InvalidCredentials",
    "InvalidVerificationToken",
    "NotAuthenticated",
    "PermissionDenied",
    "RateLimitUnavailable",
    "TooManyRequests",
]
