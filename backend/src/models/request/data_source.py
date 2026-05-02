from typing import Literal, Optional
from pydantic import BaseModel, Field


DataSourceType = Literal["postgresql", "redshift", "trino"]


class PostgresConfig(BaseModel):
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    connection_timeout: int = 10
    pool_size: int = 5
    max_overflow: int = 10


class RedshiftConfig(BaseModel):
    host: str
    port: int = 5439
    database: str
    username: str
    password: str
    cluster_id: Optional[str] = None
    region: Optional[str] = None
    ssl_mode: str = "require"
    connection_timeout: int = 10


class TrinoConfig(BaseModel):
    coordinator_url: str  # e.g. http://trino-host:8080
    catalog: str
    trino_schema: Optional[str] = None  # renamed to avoid shadowing BaseModel.schema
    username: str
    password: Optional[str] = None


class DataSourceCreate(BaseModel):
    name: str = Field(..., max_length=255)
    type: DataSourceType
    description: Optional[str] = None
    config: dict  # validated loosely; type-specific validation done in service


class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[DataSourceType] = None
    description: Optional[str] = None
    config: Optional[dict] = None


class ConnectionTestRequest(BaseModel):
    type: DataSourceType
    config: dict
