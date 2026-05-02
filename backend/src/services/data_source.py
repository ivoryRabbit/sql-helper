import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from adapters.postgres import PostgresAdapter
from adapters.redshift import RedshiftAdapter
from adapters.trino import TrinoAdapter
from models.entities import DataSource
from models.request.data_source import DataSourceCreate, DataSourceUpdate
from models.response.data_source import (
    ConnectionTestResponse,
    DataSourceResponse,
    HealthCheckResponse,
    SyncResponse,
)
from repositories.data_source import DataSourceRepository
from utils.crypto import EncryptionService

logger = logging.getLogger(__name__)

_SENSITIVE_FIELDS = {"password"}

_ADAPTERS = {
    "postgresql": PostgresAdapter(),
    "redshift": RedshiftAdapter(),
    "trino": TrinoAdapter(),
}


class DataSourceService:
    def __init__(
        self,
        repository: DataSourceRepository,
        encryption: EncryptionService,
    ) -> None:
        self._repo = repository
        self._enc = encryption

    # ── CRUD ─────────────────────────────────────────────────────────────────

    async def list(self) -> list[DataSourceResponse]:
        sources = await self._repo.get_all()
        return [self._to_response(s) for s in sources]

    async def get(self, id: UUID) -> DataSourceResponse:
        source = await self._repo.get(id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        return self._to_response(source)

    async def create(self, request: DataSourceCreate) -> DataSourceResponse:
        if await self._repo.get_by_name(request.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Data source '{request.name}' already exists",
            )
        config = self._encrypt_config(request.config)
        source = await self._repo.create(
            name=request.name,
            type=request.type,
            description=request.description,
            config=config,
        )
        logger.info("Data source created: id=%s name=%r type=%s", source.id, source.name, source.type)
        return self._to_response(source)

    async def update(self, id: UUID, request: DataSourceUpdate) -> DataSourceResponse:
        source = await self._repo.get(id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

        updates = request.model_dump(exclude_unset=True)
        if "config" in updates:
            updates["config"] = self._encrypt_config(updates["config"])
        if "name" in updates and updates["name"] != source.name:
            if await self._repo.get_by_name(updates["name"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Data source '{updates['name']}' already exists",
                )

        updated = await self._repo.update(id, **updates)
        return self._to_response(updated)

    async def delete(self, id: UUID) -> None:
        deleted = await self._repo.delete(id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        logger.info("Data source deleted: id=%s", id)

    # ── Connection test ───────────────────────────────────────────────────────

    async def test_connection_direct(self, db_type: str, config: dict) -> ConnectionTestResponse:
        host = config.get("host", "?")
        logger.info("Testing connection (direct): type=%s host=%s", db_type, host)
        plain_config = self._decrypt_config(dict(config))
        try:
            await self._connect(db_type, plain_config)
            logger.info("Connection test passed: type=%s host=%s", db_type, host)
            return ConnectionTestResponse(success=True, message="Connection successful")
        except Exception as exc:
            logger.warning("Connection test failed: type=%s host=%s error=%s", db_type, host, exc)
            return ConnectionTestResponse(success=False, message=str(exc))

    async def test_connection(self, id: UUID) -> ConnectionTestResponse:
        source = await self._repo.get(id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

        logger.info("Testing connection: id=%s name=%r type=%s", id, source.name, source.type)
        config = self._decrypt_config(dict(source.config))
        try:
            await self._connect(source.type, config)
            await self._repo.update(id, status="connected")
            logger.info("Connection test passed: id=%s name=%r", id, source.name)
            return ConnectionTestResponse(success=True, message="Connection successful")
        except Exception as exc:
            await self._repo.update(id, status="error")
            logger.warning("Connection test failed: id=%s name=%r error=%s", id, source.name, exc)
            return ConnectionTestResponse(success=False, message=str(exc))

    # ── Health check ──────────────────────────────────────────────────────────

    async def health_check(self, id: UUID) -> HealthCheckResponse:
        source = await self._repo.get(id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")

        config = self._decrypt_config(dict(source.config))
        checked_at = datetime.now(timezone.utc)
        try:
            await self._connect(source.type, config)
            await self._repo.update(id, status="connected")
            return HealthCheckResponse(
                data_source_id=id,
                status="connected",
                is_reachable=True,
                message="Connection healthy",
                checked_at=checked_at,
            )
        except Exception as exc:
            await self._repo.update(id, status="error")
            return HealthCheckResponse(
                data_source_id=id,
                status="error",
                is_reachable=False,
                message=str(exc),
                checked_at=checked_at,
            )

    # ── Catalog sync ──────────────────────────────────────────────────────────

    async def sync(self, id: UUID) -> SyncResponse:
        """Verify the source exists and return its ID for the controller to trigger refresh."""
        source = await self._repo.get(id)
        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found")
        return source

    async def mark_synced(self, id: UUID) -> None:
        await self._repo.update(id, last_synced=datetime.now(timezone.utc), status="connected")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _encrypt_config(self, config: dict) -> dict:
        config = dict(config)
        for field in _SENSITIVE_FIELDS:
            if field in config and config[field]:
                config[field] = self._enc.encrypt(str(config[field]))
        return config

    def _decrypt_config(self, config: dict) -> dict:
        for field in _SENSITIVE_FIELDS:
            if field in config and config[field]:
                try:
                    config[field] = self._enc.decrypt(config[field])
                except Exception:
                    pass  # already plaintext (e.g. legacy row)
        return config

    def _to_response(self, source: DataSource) -> DataSourceResponse:
        safe_config = {k: v for k, v in source.config.items() if k not in _SENSITIVE_FIELDS}
        return DataSourceResponse(
            id=source.id,
            name=source.name,
            type=source.type,
            description=source.description,
            config=safe_config,
            status=source.status,
            last_synced=source.last_synced,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )

    async def _connect(self, db_type: str, config: dict) -> None:
        adapter = _ADAPTERS.get(db_type)
        if adapter is None:
            raise ValueError(f"Unsupported data source type: {db_type}")
        await adapter.test_connection(config)
