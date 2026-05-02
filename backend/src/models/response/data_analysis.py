from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ColumnInfo(BaseModel):
    name: str
    type: str


class ColumnStats(BaseModel):
    column_name: str
    data_type: str
    null_count: int
    unique_count: int
    total_count: int
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    avg_value: Optional[float] = None
    summary_stats: Optional[dict] = None


class VisualizationConfig(BaseModel):
    type: str  # line_chart | bar_chart | scatter_plot | table
    title: str
    config: dict


class InsightItem(BaseModel):
    insight_type: str
    insight_text: str
    confidence_score: Optional[float] = None


class AnalysisExecutionResponse(BaseModel):
    id: UUID
    sql_generation_id: Optional[UUID]
    data_source_id: Optional[UUID]
    executed_sql: str
    execution_time_ms: Optional[int]
    row_count: Optional[int]
    status: str
    error_message: Optional[str]
    columns: list[ColumnInfo]
    data: list[dict[str, Any]]
    statistics: list[ColumnStats]
    insights: list[InsightItem]
    visualizations: list[VisualizationConfig]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisHistoryItem(BaseModel):
    id: UUID
    sql_generation_id: Optional[UUID]
    data_source_id: Optional[UUID]
    executed_sql: str
    execution_time_ms: Optional[int]
    row_count: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ExportResponse(BaseModel):
    analysis_id: UUID
    format: str
    download_url: str
    expires_in_seconds: int = 3600
