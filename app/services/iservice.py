from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from app.core.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class IService(ABC, Generic[ModelT]):
    @abstractmethod
    async def get(self, obj_id: int) -> ModelT | None: ...

    @abstractmethod
    async def get_or_404(self, obj_id: int) -> ModelT: ...

    @abstractmethod
    async def get_list(
        self,
        limit: int | None = None,
        offset: int | None = None,
        **filters: Any,
    ) -> Sequence[ModelT]: ...

    @abstractmethod
    async def delete(self, obj_id: int) -> None: ...
