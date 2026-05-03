from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# ── Semantic search (merged from data_discovery) ──────────────────────────────

class SemanticSearchResultItem(BaseModel):
    type: str  # "table" | "column"
    table_id: Optional[UUID] = None
    schema_name: str
    table_name: str
    column_name: Optional[str] = None
    description: Optional[str] = None
    relevance_score: float
    snippet: str


class SemanticSearchResponse(BaseModel):
    query: str
    results: list[SemanticSearchResultItem]
    total_found: int
    search_time_ms: int


class RecommendedTable(BaseModel):
    table_id: Optional[UUID] = None
    table_name: str
    schema_name: str
    reason: str
    confidence: float


class RecommendationResponse(BaseModel):
    query: str
    recommended_tables: list[RecommendedTable]
    suggested_questions: list[str]


class SearchHistoryItem(BaseModel):
    id: UUID
    query: str
    search_type: Optional[str] = None
    results_count: Optional[int] = None
    search_time_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ColumnResponse(BaseModel):
    id: UUID
    column_name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    is_primary_key: bool
    is_foreign_key: bool
    references_column: Optional[str]
    source_description: Optional[str]
    user_description: Optional[str]
    ordinal_position: int

    model_config = {"from_attributes": True}


class TableResponse(BaseModel):
    id: UUID
    schema_id: UUID
    schema_name: str
    table_name: str
    table_type: str
    row_count: int
    source_description: Optional[str]
    user_description: Optional[str]
    tags: Optional[list[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TableDetailResponse(TableResponse):
    columns: list[ColumnResponse]


class SchemaResponse(BaseModel):
    id: UUID
    data_source_id: UUID
    schema_name: str
    table_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CatalogSourceResponse(BaseModel):
    data_source_id: UUID
    schemas: list[SchemaResponse]
    tables: list[TableResponse]


class ColumnSearchResult(BaseModel):
    column: ColumnResponse
    table_name: str
    schema_name: str


class SearchResponse(BaseModel):
    tables: list[TableResponse]
    columns: list[ColumnSearchResult]


class CatalogStatsResponse(BaseModel):
    total_schemas: int
    total_tables: int
    total_columns: int
    data_sources: int
    last_updated: Optional[datetime]


class CatalogRefreshResponse(BaseModel):
    data_source_id: UUID
    message: str
    schemas_synced: int = 0
    tables_synced: int = 0
    columns_synced: int = 0
    workflow_id: Optional[str] = None
