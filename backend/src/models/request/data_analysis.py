from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    include_statistics: bool = True
    generate_insights: bool = True
    limit_rows: int = Field(5000, ge=1, le=50000)


class AnalysisExecuteRequest(BaseModel):
    sql: str = Field(..., min_length=1)
    data_source_id: UUID
    sql_generation_id: Optional[UUID] = None
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)


class DataExportRequest(BaseModel):
    analysis_id: UUID
    format: Literal["csv", "json"] = "csv"
    include_metadata: bool = True
