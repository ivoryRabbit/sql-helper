from typing import AsyncGenerator

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from components.database_manager import DatabaseManager
from configs.container import container
from repositories.dashboard import DashboardRepository, DashboardWidgetRepository
from repositories.data_analysis import (
    AnalysisExecutionRepository,
    AnalysisInsightRepository,
    AnalysisResultRepository,
)
from repositories.data_catalog import DataCatalogRepository
from repositories.data_source import DataSourceRepository
from repositories.search_history import SearchHistoryRepository
from repositories.table_document import TableDocumentRepository
from repositories.sql_assistant import (
    ConversationMessageRepository,
    ConversationSessionRepository,
    SqlGenerationRepository,
)
from services.dashboard import DashboardService
from services.data_analysis import DataAnalysisService
from services.data_catalog import DataCatalogService
from services.data_source import DataSourceService
from services.sql_assistant import SqlAssistantService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    db: DatabaseManager = container.database_manager()
    if not db.is_available:
        raise HTTPException(status_code=503, detail="Database is currently unavailable.")
    async with db.get_session() as session:
        yield session


# ── per-feature service factories ────────────────────────────────────────────
# Repositories are request-scoped (need an AsyncSession) so they are
# constructed here and injected into the container's Factory providers at
# call time.  Application-scoped dependencies (encryption, LLM client, etc.)
# are resolved by the container automatically.


def get_data_source_service(
    session: AsyncSession = Depends(get_session),
) -> DataSourceService:
    return container.data_source_service(
        repository=DataSourceRepository(session),
    )


def get_data_catalog_service(
    session: AsyncSession = Depends(get_session),
) -> DataCatalogService:
    return container.data_catalog_service(
        repo=DataCatalogRepository(session),
        data_source_repo=DataSourceRepository(session),
        doc_repo=TableDocumentRepository(session),
        history_repo=SearchHistoryRepository(session),
    )


def get_sql_assistant_service(
    session: AsyncSession = Depends(get_session),
) -> SqlAssistantService:
    return container.sql_assistant_service(
        generation_repo=SqlGenerationRepository(session),
        session_repo=ConversationSessionRepository(session),
        message_repo=ConversationMessageRepository(session),
        doc_repo=TableDocumentRepository(session),
    )


def get_data_analysis_service(
    session: AsyncSession = Depends(get_session),
) -> DataAnalysisService:
    return container.data_analysis_service(
        execution_repo=AnalysisExecutionRepository(session),
        result_repo=AnalysisResultRepository(session),
        insight_repo=AnalysisInsightRepository(session),
        data_source_repo=DataSourceRepository(session),
    )


def get_dashboard_service(
    session: AsyncSession = Depends(get_session),
) -> DashboardService:
    return container.dashboard_service(
        dashboard_repo=DashboardRepository(session),
        widget_repo=DashboardWidgetRepository(session),
    )
