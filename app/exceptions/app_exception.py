from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str | None = None,
        info: dict[str, Any] | None = None,
        http_status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.info = info or {}
        self.http_status_code = http_status_code or 500
        self.headers = headers or {}

    def __str__(self) -> str:
        return f"{self.message} http_status_code={self.http_status_code} info={self.info}"
