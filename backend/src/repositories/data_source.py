from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import DataSource
from repositories.base import BaseRepository


class DataSourceRepository(BaseRepository[DataSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DataSource)

    async def get_by_name(self, name: str) -> Optional[DataSource]:
        result = await self._session.execute(
            select(DataSource).where(DataSource.name == name)
        )
        return result.scalar_one_or_none()
