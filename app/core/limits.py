"""Value bounds shared across schemas and services."""

from typing import Final

NAME_MIN: Final = 1
NAME_MAX: Final = 64
PASSWORD_MIN: Final = 8
PASSWORD_MAX: Final = 72

ORG_NAME_MIN: Final = 2
ORG_NAME_MAX: Final = 128
ORG_SLUG_MAX: Final = 64

API_KEY_NAME_MAX: Final = 64
API_KEY_PREFIX_LEN: Final = 8

PAGE_SIZE_DEFAULT: Final = 20
PAGE_SIZE_MAX: Final = 100

SCORE_MIN: Final = 0
SCORE_MAX: Final = 100

VERIFICATION_TOKEN_MIN: Final = 10
VERIFICATION_TOKEN_MAX: Final = 128
