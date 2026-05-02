from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from components.database_manager import ModelBase

T = TypeVar("T", bound=ModelBase)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self._session = session
        self._model = model

    async def get(self, id: UUID) -> Optional[T]:
        result = await self._session.execute(
            select(self._model).where(self._model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[T]:
        result = await self._session.execute(select(self._model))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        instance = await self.get(id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        instance = await self.get(id)
        if instance is None:
            return False
        await self._session.delete(instance)
        await self._session.flush()
        return True
