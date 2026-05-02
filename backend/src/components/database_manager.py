import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from configs.settings import Settings

logger = logging.getLogger(__name__)


class ModelBase(DeclarativeBase):
    metadata = MetaData(schema="data_catalog")


class DatabaseManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._is_available: bool = False

    @property
    def is_available(self) -> bool:
        return self._is_available

    async def initialize(self) -> None:
        try:
            self._engine = create_async_engine(
                self._settings.database_url,
                pool_size=self._settings.db_pool_size,
                max_overflow=self._settings.db_max_overflow,
                pool_recycle=self._settings.db_pool_recycle,
                echo=False,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
            await self.create_tables()
            self._is_available = True
            logger.info("Database connected successfully.")
        except Exception as e:
            self._is_available = False
            logger.warning(
                "Database unavailable — application starting in degraded mode. "
                "Reason: %s",
                e,
            )

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()

    async def create_tables(self) -> None:
        from models import entities  # noqa: F401 — registers all ORM metadata

        async with self._engine.begin() as conn:
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS data_catalog"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(ModelBase.metadata.create_all)
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_table_documents_embedding
                ON data_catalog.table_documents
                USING hnsw (embedding vector_cosine_ops)
                WITH (m=16, ef_construction=64)
            """))

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
