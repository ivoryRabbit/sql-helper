from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WidgetResponse(BaseModel):
    id: UUID
    dashboard_id: UUID
    widget_type: str
    title: str
    position_x: int
    position_y: int
    width: int
    height: int
    analysis_id: Optional[UUID]
    chart_config: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    layout: str
    is_public: bool
    tags: Optional[list[str]]
    html_content: Optional[str]
    widgets: list[WidgetResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardListItem(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    layout: str
    is_public: bool
    tags: Optional[list[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardHtmlResponse(BaseModel):
    dashboard_id: UUID
    html: str


class ShareResponse(BaseModel):
    dashboard_id: UUID
    share_url: str
    expires_in_seconds: int = 3600
