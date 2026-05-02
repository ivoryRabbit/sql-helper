from dependency_injector import containers, providers

from clients.embedding import EmbeddingClient
from clients.llm import LLMClient
from clients.storage import StorageClient
from clients.temporal import TemporalClient
from components.database_manager import DatabaseManager
from configs.settings import Settings
from services.dashboard import DashboardService
from services.data_analysis import DataAnalysisService
from services.data_catalog import DataCatalogService
from services.data_source import DataSourceService
from services.sql_assistant import SqlAssistantService
from utils.crypto import EncryptionService


class AppContainer(containers.DeclarativeContainer):
    # ── Infrastructure singletons ─────────────────────────────────────────────

    settings = providers.Singleton(Settings)

    database_manager = providers.Singleton(
        DatabaseManager,
        settings=settings,
    )

    encryption = providers.Singleton(
        EncryptionService,
        key=settings.provided.encryption_key,
    )

    embedding_client = providers.Singleton(
        EmbeddingClient,
        model_name=settings.provided.embedding_model,
    )

    llm_client = providers.Singleton(
        LLMClient,
        api_key=settings.provided.openai_api_key,
    )

    storage_client = providers.Singleton(
        StorageClient,
        endpoint=settings.provided.minio_endpoint,
        access_key=settings.provided.minio_access_key,
        secret_key=settings.provided.minio_secret_key,
    )

    temporal_client = providers.Singleton(
        TemporalClient,
        address=settings.provided.temporal_address,
    )

    # ── Service factories ─────────────────────────────────────────────────────
    # Repository dependencies are request-scoped (need an AsyncSession) so they
    # are passed as kwargs at call time in dependencies.py.  Only application-
    # scoped (singleton) dependencies are wired here.

    data_source_service = providers.Factory(
        DataSourceService,
        encryption=encryption,
    )

    data_catalog_service = providers.Factory(
        DataCatalogService,
        encryption=encryption,
        embedding_client=embedding_client,
    )

    sql_assistant_service = providers.Factory(
        SqlAssistantService,
        embedding_client=embedding_client,
        llm_client=llm_client,
    )

    data_analysis_service = providers.Factory(
        DataAnalysisService,
        encryption=encryption,
        storage=storage_client,
    )

    dashboard_service = providers.Factory(
        DashboardService,
        storage=storage_client,
    )


# Module-level singleton — initialized once at app startup
container = AppContainer()
