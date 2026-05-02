from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import AnalysisExecution, AnalysisInsight, AnalysisResult
from repositories.base import BaseRepository


class AnalysisExecutionRepository(BaseRepository[AnalysisExecution]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnalysisExecution)

    async def list_recent(self, limit: int = 50) -> list[AnalysisExecution]:
        result = await self._session.execute(
            select(AnalysisExecution)
            .order_by(AnalysisExecution.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnalysisResult)

    async def get_by_analysis(self, analysis_id: UUID) -> list[AnalysisResult]:
        result = await self._session.execute(
            select(AnalysisResult).where(AnalysisResult.analysis_id == analysis_id)
        )
        return list(result.scalars().all())


class AnalysisInsightRepository(BaseRepository[AnalysisInsight]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AnalysisInsight)

    async def get_by_analysis(self, analysis_id: UUID) -> list[AnalysisInsight]:
        result = await self._session.execute(
            select(AnalysisInsight).where(AnalysisInsight.analysis_id == analysis_id)
        )
        return list(result.scalars().all())
