from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DataSourceResponse(BaseModel):
    id: UUID
    name: str
    type: str
    description: Optional[str]
    config: dict  # password field is stripped before returning
    status: str
    last_synced: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str


class HealthCheckResponse(BaseModel):
    data_source_id: UUID
    status: str
    is_reachable: bool
    message: str
    checked_at: datetime


class SyncResponse(BaseModel):
    data_source_id: UUID
    message: str
    schemas_synced: int = 0
    tables_synced: int = 0
    columns_synced: int = 0
