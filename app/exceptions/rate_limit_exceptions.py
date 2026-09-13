from app.exceptions.app_exception import AppException


class TooManyRequests(AppException):
    def __init__(self, retry_after: int, limit: int) -> None:
        super().__init__(
            message="Too many requests",
            info={"retry_after": retry_after},
            http_status_code=429,
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )


class RateLimitUnavailable(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Service temporarily unavailable",
            http_status_code=503,
        )
