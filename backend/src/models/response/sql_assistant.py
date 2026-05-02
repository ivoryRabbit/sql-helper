from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    syntax_errors: list[str] = []
    security_issues: list[str] = []
    suggestions: list[str] = []


# ── SSE event payloads (serialized as individual JSON lines, not HTTP response models) ──

class SqlChunkEvent(BaseModel):
    type: Literal["sql_chunk"] = "sql_chunk"
    content: str
    generation_id: UUID


class GenerationCompleteEvent(BaseModel):
    type: Literal["generation_complete"] = "generation_complete"
    generation_id: UUID
    sql: Optional[str]
    explanation: Optional[str]
    confidence_score: Optional[float]
    validation: ValidationResult


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
    generation_id: Optional[UUID] = None


# ── Standard response models ──

class ValidationResponse(BaseModel):
    sql: str
    validation: ValidationResult


class ExplainResponse(BaseModel):
    sql: str
    explanation: str


class OptimizeResponse(BaseModel):
    sql: str
    suggestions: list[str]
    optimized_sql: Optional[str] = None


class SqlGenerationHistoryItem(BaseModel):
    id: UUID
    user_query: str
    generated_sql: Optional[str]
    validation_status: str
    confidence_score: Optional[float]
    llm_model: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: UUID
    title: str
    data_source_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    sql_generation_id: Optional[UUID]
    extra_metadata: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse]
