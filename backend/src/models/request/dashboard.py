from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Literal["grid", "free"] = "grid"
    is_public: bool = False
    tags: Optional[list[str]] = None


class DashboardUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[Literal["grid", "free"]] = None
    is_public: Optional[bool] = None
    tags: Optional[list[str]] = None


class WidgetCreateRequest(BaseModel):
    widget_type: Literal["chart", "table", "metric", "text"]
    title: str = Field(..., min_length=1, max_length=255)
    position_x: int = Field(0, ge=0)
    position_y: int = Field(0, ge=0)
    width: int = Field(4, ge=1)
    height: int = Field(3, ge=1)
    analysis_id: Optional[UUID] = None
    chart_config: Optional[dict] = None


class WidgetUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    position_x: Optional[int] = Field(None, ge=0)
    position_y: Optional[int] = Field(None, ge=0)
    width: Optional[int] = Field(None, ge=1)
    height: Optional[int] = Field(None, ge=1)
    chart_config: Optional[dict] = None
