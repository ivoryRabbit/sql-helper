from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerationOptions(BaseModel):
    include_explanation: bool = True
    sql_dialect: Literal["postgresql", "mysql", "sqlite"] = "postgresql"


class GenerateRequest(BaseModel):
    query: str = Field(..., min_length=1)
    data_source_id: Optional[UUID] = None
    selected_tables: Optional[list[UUID]] = None
    session_id: Optional[UUID] = None
    options: GenerationOptions = Field(default_factory=GenerationOptions)


class ValidateRequest(BaseModel):
    sql: str = Field(..., min_length=1)
    data_source_id: Optional[UUID] = None


class ExplainRequest(BaseModel):
    sql: str = Field(..., min_length=1)
    dialect: Literal["postgresql", "mysql", "sqlite"] = "postgresql"


class OptimizeRequest(BaseModel):
    sql: str = Field(..., min_length=1)
    dialect: Literal["postgresql", "mysql", "sqlite"] = "postgresql"


class CreateSessionRequest(BaseModel):
    title: str = Field("New Conversation", max_length=500)
    data_source_id: Optional[UUID] = None
