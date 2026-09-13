from app.exceptions.app_exception import AppException


class InvalidCredentials(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            http_status_code=401,
        )


class EmailNotVerified(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Email is not verified",
            http_status_code=403,
        )


class AccountDisabled(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Account is disabled",
            http_status_code=403,
        )


class InvalidVerificationToken(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Verification link is invalid or has expired",
            http_status_code=400,
        )


class NotAuthenticated(AppException):
    def __init__(self, reason: str = "Authentication required") -> None:
        super().__init__(message=reason, http_status_code=401)


class PermissionDenied(AppException):
    def __init__(self, action: str | None = None) -> None:
        super().__init__(
            message="Not enough permissions",
            info={"action": action} if action else {},
            http_status_code=403,
        )
