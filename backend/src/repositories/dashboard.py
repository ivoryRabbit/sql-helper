from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import Dashboard, DashboardWidget
from repositories.base import BaseRepository


class DashboardRepository(BaseRepository[Dashboard]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Dashboard)

    async def list_all(self) -> list[Dashboard]:
        result = await self._session.execute(
            select(Dashboard).order_by(Dashboard.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_widgets(self, dashboard_id: UUID) -> list[DashboardWidget]:
        result = await self._session.execute(
            select(DashboardWidget)
            .where(DashboardWidget.dashboard_id == dashboard_id)
            .order_by(DashboardWidget.position_y, DashboardWidget.position_x)
        )
        return list(result.scalars().all())


class DashboardWidgetRepository(BaseRepository[DashboardWidget]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DashboardWidget)

    async def get_by_dashboard(self, dashboard_id: UUID) -> list[DashboardWidget]:
        result = await self._session.execute(
            select(DashboardWidget)
            .where(DashboardWidget.dashboard_id == dashboard_id)
            .order_by(DashboardWidget.position_y, DashboardWidget.position_x)
        )
        return list(result.scalars().all())
