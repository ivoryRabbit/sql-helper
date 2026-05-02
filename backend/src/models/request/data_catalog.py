from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogRefreshRequest(BaseModel):
    data_source_id: UUID


class SemanticSearchFilters(BaseModel):
    schema_name: Optional[str] = None
    table_types: Optional[list[str]] = None


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    data_source_ids: Optional[list[UUID]] = None
    search_type: str = Field("both", pattern="^(tables|columns|both)$")
    limit: int = Field(10, ge=1, le=100)
    filters: Optional[SemanticSearchFilters] = None


class SimilarTableRequest(BaseModel):
    table_id: UUID
    limit: int = Field(5, ge=1, le=20)


class UpdateDescriptionRequest(BaseModel):
    description: Optional[str] = None
