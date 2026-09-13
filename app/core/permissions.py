"""Role permission matrix."""

from typing import TYPE_CHECKING

from app.core.config import settings
from app.models.users import UserRole

if TYPE_CHECKING:
    from app.models.users import User

ROLE_RANK: dict[UserRole, int] = {
    UserRole.SUPER_ADMIN: 0,
    UserRole.OWNER: 1,
    UserRole.ADMIN: 2,
    UserRole.MANAGER: 3,
    UserRole.OPERATOR: 4,
}

PLATFORM_STAFF = frozenset({UserRole.SUPER_ADMIN})
WHOLE_ORG = frozenset({UserRole.OWNER, UserRole.ADMIN})
MANAGE_PEOPLE = frozenset({UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER})
MANAGE_API_KEYS = frozenset({UserRole.OWNER})
VERIFY_SCORES = frozenset({UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER})


def is_platform_staff(user: "User") -> bool:
    return user.role in PLATFORM_STAFF


def sees_whole_org(user: "User") -> bool:
    return user.role in WHOLE_ORG


def can_manage_people(user: "User") -> bool:
    return user.role in MANAGE_PEOPLE


def can_manage_api_keys(user: "User") -> bool:
    return user.role in MANAGE_API_KEYS


def can_verify_scores(user: "User") -> bool:
    """Operators never verify scores, including their own."""
    return user.role in VERIFY_SCORES


def is_demo(user: "User") -> bool:
    """The shared demo account, which may only read."""
    return settings.demo_enabled and user.email == settings.demo_email
