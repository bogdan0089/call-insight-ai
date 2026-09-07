from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.exceptions import AlreadyExistsError, DatabaseError, ForeignKeyViolationError
from app.repositories.irepository import IAsyncRepository

ModelT = TypeVar("ModelT", bound=Base)


class SqlalchemyAsyncRepository(IAsyncRepository[ModelT], Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self._flush()
        return obj

    async def get(self, obj_id: int) -> ModelT | None:
        try:
            return await self.session.get(self.model, obj_id)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc

    async def get_by(self, **filters: Any) -> ModelT | None:
        stmt = select(self.model).filter_by(**filters)
        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc
        return result.scalar_one_or_none()

    async def get_list_by(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> Sequence[ModelT]:
        stmt = select(self.model).filter_by(**filters)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc
        return result.scalars().all()

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self._flush()

    async def _flush(self) -> None:
        try:
            await self.session.flush()
        except IntegrityError as exc:
            detail = str(exc.orig).splitlines()[0]
            message = detail.lower()
            if "unique" in message:
                raise AlreadyExistsError(constraint=detail) from exc
            if "foreign key" in message:
                raise ForeignKeyViolationError(constraint=detail) from exc
            raise DatabaseError(exc=exc) from exc
        except SQLAlchemyError as exc:
            raise DatabaseError(exc=exc) from exc
