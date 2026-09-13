"""Value bounds shared across schemas and services."""

from typing import Final

NAME_MIN: Final = 1
NAME_MAX: Final = 64
PASSWORD_MIN: Final = 8
PASSWORD_MAX: Final = 72

VERIFICATION_TOKEN_MIN: Final = 10
VERIFICATION_TOKEN_MAX: Final = 128
