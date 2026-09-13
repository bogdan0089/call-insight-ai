"""Role permission matrix."""

from typing import TYPE_CHECKING

from app.models.users import UserRole

if TYPE_CHECKING:
    from app.models.users import User

PLATFORM_STAFF = frozenset({UserRole.SUPER_ADMIN})
WHOLE_ORG = frozenset({UserRole.OWNER, UserRole.ADMIN})
MANAGE_PEOPLE = frozenset({UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER})
VERIFY_SCORES = frozenset({UserRole.OWNER, UserRole.ADMIN, UserRole.MANAGER})


def is_platform_staff(user: "User") -> bool:
    return user.role in PLATFORM_STAFF


def sees_whole_org(user: "User") -> bool:
    return user.role in WHOLE_ORG


def can_manage_people(user: "User") -> bool:
    return user.role in MANAGE_PEOPLE


def can_verify_scores(user: "User") -> bool:
    """Operators never verify scores, including their own."""
    return user.role in VERIFY_SCORES

