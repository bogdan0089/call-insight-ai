from sqlalchemy import ColumnElement, and_, or_, select

from app.core.permissions import is_platform_staff, sees_whole_org
from app.models.calls import Call
from app.models.checklist import ChecklistItem
from app.models.users import User, UserRole


def visible_calls(user: User) -> ColumnElement[bool] | None:
    """Condition limiting calls to what the user may see; None means unrestricted."""
    if is_platform_staff(user):
        return None

    same_org = Call.organization_id == user.organization_id

    if sees_whole_org(user):
        return same_org

    if user.role is UserRole.MANAGER:
        team = select(User.id).where(User.manager_id == user.id)
        own_or_team = or_(Call.operator_id == user.id, Call.operator_id.in_(team))
        return and_(same_org, own_or_team)

    return and_(same_org, Call.operator_id == user.id)


def visible_operators(user: User) -> ColumnElement[bool] | None:
    if is_platform_staff(user):
        return None

    same_org = User.organization_id == user.organization_id

    if sees_whole_org(user):
        return same_org

    if user.role is UserRole.MANAGER:
        return and_(same_org, or_(User.id == user.id, User.manager_id == user.id))

    return and_(same_org, User.id == user.id)


def visible_checklist(user: User) -> ColumnElement[bool] | None:
    if is_platform_staff(user):
        return None
    return ChecklistItem.organization_id == user.organization_id
