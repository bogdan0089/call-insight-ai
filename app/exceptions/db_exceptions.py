from typing import Any

from app.exceptions.app_exception import AppException


class DatabaseError(AppException):
    def __init__(self, exc: Exception | None = None) -> None:
        super().__init__(
            message="Database operation error",
            info={"error": str(exc)} if exc else {},
            http_status_code=500,
        )


class EntityNotFound(AppException):
    def __init__(self, entity: str, **identifiers: Any) -> None:
        super().__init__(
            message=f"{entity} not found",
            info=identifiers,
            http_status_code=404,
        )


class ConstraintViolationError(AppException):
    def __init__(
        self,
        message: str = "Constraint violation occurred",
        constraint: str | None = None,
        http_status_code: int = 400,
    ) -> None:
        super().__init__(
            message=message,
            info={"constraint": constraint} if constraint else {},
            http_status_code=http_status_code,
        )


class AlreadyExistsError(ConstraintViolationError):
    def __init__(self, constraint: str | None = None) -> None:
        super().__init__(
            message="Entity already exists",
            constraint=constraint,
            http_status_code=409,
        )


class ForeignKeyViolationError(ConstraintViolationError):
    def __init__(self, constraint: str | None = None) -> None:
        super().__init__(
            message="Foreign key violation",
            constraint=constraint,
            http_status_code=422,
        )
