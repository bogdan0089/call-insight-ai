"""Whitelisted sorting shared by list endpoints."""

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, TypeVar

from sqlalchemy import ColumnElement, Select

FieldT = TypeVar("FieldT", bound=StrEnum)


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


def apply_sort(
    stmt: Select[Any],
    columns: Mapping[FieldT, ColumnElement[Any]],
    field: FieldT,
    order: SortOrder,
    tiebreaker: ColumnElement[Any],
) -> Select[Any]:
    """Order by a field with NULLs last and a stable tiebreaker."""
    column = columns[field]
    if order is SortOrder.ASC:
        return stmt.order_by(column.asc().nullslast(), tiebreaker.asc())
    return stmt.order_by(column.desc().nullslast(), tiebreaker.desc())
