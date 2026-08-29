from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from app.core.db import Base


ModelT = TypeVar("ModelT", bound=Base)


class IAsyncRepository(ABC, Generic[ModelT]):


    @abstractmethod
    async def create(self, obj: ModelT) -> ModelT:
        pass


    @abstractmethod
    async def get(self, obj_id: int) -> ModelT | None:
        pass


    @abstractmethod
    async def get_by(self, **filters: Any) -> ModelT | None:
        pass


    @abstractmethod
    async def get_list_by(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any
    ) -> Sequence[ModelT]: ...


    @abstractmethod
    async def delete(self, obj: ModelT) -> None:
        pass