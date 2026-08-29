from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from app.core.db import Base
from app.exceptions import EntityNotFound
from app.repositories.base_repository import SqlalchemyAsyncRepository
from app.services.iservice import IService

ModelT = TypeVar("ModelT", bound=Base)
RepoT = TypeVar("RepoT", bound=SqlalchemyAsyncRepository)


class BaseService(IService[ModelT], Generic[ModelT, RepoT]):
    entity_name: str

    def __init__(self, repo: RepoT) -> None:
        self.repo = repo

    async def get(self, obj_id: int) -> ModelT | None:
        return await self.repo.get(obj_id)

    async def get_or_404(self, obj_id: int) -> ModelT:
        obj = await self.repo.get(obj_id)
        if obj is None:
            raise EntityNotFound(entity=self.entity_name, id=obj_id)
        return obj

    async def get_list(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> Sequence[ModelT]:
        return await self.repo.get_list_by(limit=limit, offset=offset, **filters)

    async def delete(self, obj_id: int) -> None:
        obj = await self.get_or_404(obj_id)
        await self.repo.delete(obj)
