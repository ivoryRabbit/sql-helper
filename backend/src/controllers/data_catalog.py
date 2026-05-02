from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from dependencies import get_data_catalog_service
from models.request.data_catalog import (
    CatalogRefreshRequest,
    SemanticSearchRequest,
    SimilarTableRequest,
    UpdateDescriptionRequest,
)
from models.response.data_catalog import (
    CatalogRefreshResponse,
    CatalogSourceResponse,
    CatalogStatsResponse,
    ColumnResponse,
    RecommendationResponse,
    SchemaResponse,
    SearchHistoryItem,
    SearchResponse,
    SemanticSearchResponse,
    TableDetailResponse,
    TableResponse,
)
from services.data_catalog import DataCatalogService

router = APIRouter(prefix="/data-catalog", tags=["data-catalog"])


@router.get("/sources/{data_source_id}", response_model=CatalogSourceResponse)
async def get_catalog_by_source(
    data_source_id: UUID,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> CatalogSourceResponse:
    return await service.get_by_source(data_source_id)


@router.get("/tables", response_model=list[TableResponse])
async def list_tables(
    data_source_id: Optional[UUID] = Query(None),
    schema_id: Optional[UUID] = Query(None),
    table_type: Optional[str] = Query(None, pattern="^(table|view)$"),
    search: Optional[str] = Query(None),
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> list[TableResponse]:
    return await service.list_tables(data_source_id, schema_id, table_type, search)


@router.get("/tables/{table_id}", response_model=TableDetailResponse)
async def get_table(
    table_id: UUID,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> TableDetailResponse:
    return await service.get_table(table_id)


@router.get("/schemas", response_model=list[SchemaResponse])
async def list_schemas(
    data_source_id: Optional[UUID] = Query(None),
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> list[SchemaResponse]:
    return await service.list_schemas(data_source_id)


@router.get("/search", response_model=SearchResponse)
async def search_catalog(
    q: str = Query(..., min_length=1),
    type: Optional[str] = Query(None, pattern="^(table|column)$"),
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> SearchResponse:
    return await service.search(q, type)


@router.post("/refresh", response_model=CatalogRefreshResponse)
async def refresh_catalog(
    request: CatalogRefreshRequest,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> CatalogRefreshResponse:
    return await service.refresh(request)


@router.get("/stats", response_model=CatalogStatsResponse)
async def get_catalog_stats(
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> CatalogStatsResponse:
    return await service.get_stats()


# ── Semantic search endpoints (merged from data-discovery) ────────────────────

@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> SemanticSearchResponse:
    return await service.semantic_search(request)


@router.post("/similar", response_model=SemanticSearchResponse)
async def find_similar(
    request: SimilarTableRequest,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> SemanticSearchResponse:
    return await service.find_similar(request)


@router.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    q: str = Query(..., min_length=1),
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> RecommendationResponse:
    return await service.get_recommendations(q)


@router.get("/history", response_model=list[SearchHistoryItem])
async def get_search_history(
    limit: int = Query(50, ge=1, le=200),
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> list[SearchHistoryItem]:
    return await service.get_search_history(limit)


# ── Description update endpoints ──────────────────────────────────────────────

@router.patch("/tables/{table_id}/description", response_model=TableResponse)
async def update_table_description(
    table_id: UUID,
    request: UpdateDescriptionRequest,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> TableResponse:
    return await service.update_table_description(table_id, request.description)


@router.patch("/columns/{column_id}/description", response_model=ColumnResponse)
async def update_column_description(
    column_id: UUID,
    request: UpdateDescriptionRequest,
    service: DataCatalogService = Depends(get_data_catalog_service),
) -> ColumnResponse:
    return await service.update_column_description(column_id, request.description)
