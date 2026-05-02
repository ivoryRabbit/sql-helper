from uuid import UUID

from fastapi import APIRouter, Depends, status

from dependencies import get_data_catalog_service, get_data_source_service
from models.request.data_source import ConnectionTestRequest, DataSourceCreate, DataSourceUpdate
from models.request.data_catalog import CatalogRefreshRequest
from models.response.data_source import (
    ConnectionTestResponse,
    DataSourceResponse,
    HealthCheckResponse,
    SyncResponse,
)
from services.data_catalog import DataCatalogService
from services.data_source import DataSourceService

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("", response_model=list[DataSourceResponse])
async def list_data_sources(
    service: DataSourceService = Depends(get_data_source_service),
) -> list[DataSourceResponse]:
    return await service.list()


@router.get("/{id}", response_model=DataSourceResponse)
async def get_data_source(
    id: UUID,
    service: DataSourceService = Depends(get_data_source_service),
) -> DataSourceResponse:
    return await service.get(id)


@router.post("", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    request: DataSourceCreate,
    service: DataSourceService = Depends(get_data_source_service),
) -> DataSourceResponse:
    return await service.create(request)


@router.put("/{id}", response_model=DataSourceResponse)
async def update_data_source(
    id: UUID,
    request: DataSourceUpdate,
    service: DataSourceService = Depends(get_data_source_service),
) -> DataSourceResponse:
    return await service.update(id, request)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    id: UUID,
    service: DataSourceService = Depends(get_data_source_service),
) -> None:
    await service.delete(id)


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection_direct(
    request: ConnectionTestRequest,
    service: DataSourceService = Depends(get_data_source_service),
) -> ConnectionTestResponse:
    return await service.test_connection_direct(request.type, request.config)


@router.post("/{id}/test", response_model=ConnectionTestResponse)
async def test_connection(
    id: UUID,
    service: DataSourceService = Depends(get_data_source_service),
) -> ConnectionTestResponse:
    return await service.test_connection(id)


@router.get("/{id}/health", response_model=HealthCheckResponse)
async def health_check(
    id: UUID,
    service: DataSourceService = Depends(get_data_source_service),
) -> HealthCheckResponse:
    return await service.health_check(id)


@router.post("/{id}/sync", response_model=SyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def sync_data_source(
    id: UUID,
    ds_service: DataSourceService = Depends(get_data_source_service),
    catalog_service: DataCatalogService = Depends(get_data_catalog_service),
) -> SyncResponse:
    source = await ds_service.sync(id)
    refresh = await catalog_service.refresh(CatalogRefreshRequest(data_source_id=source.id))
    await ds_service.mark_synced(id)
    return SyncResponse(
        data_source_id=source.id,
        message=refresh.message,
        schemas_synced=refresh.schemas_synced,
        tables_synced=refresh.tables_synced,
        columns_synced=refresh.columns_synced,
    )
