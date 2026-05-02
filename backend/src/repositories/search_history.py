from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import SearchHistory


class SearchHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        query: str,
        search_type: Optional[str] = None,
        results_count: Optional[int] = None,
        search_time_ms: Optional[int] = None,
    ) -> SearchHistory:
        entry = SearchHistory(
            query=query,
            search_type=search_type,
            results_count=results_count,
            search_time_ms=search_time_ms,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list(self, limit: int = 50) -> list[SearchHistory]:
        result = await self._session.execute(
            select(SearchHistory)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
