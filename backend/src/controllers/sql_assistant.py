import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from dependencies import get_sql_assistant_service
from models.request.sql_assistant import (
    CreateSessionRequest,
    ExplainRequest,
    GenerateRequest,
    OptimizeRequest,
    ValidateRequest,
)
from models.response.sql_assistant import (
    ExplainResponse,
    OptimizeResponse,
    SessionDetailResponse,
    SessionResponse,
    SqlGenerationHistoryItem,
    ValidationResponse,
)
from services.sql_assistant import SqlAssistantService

router = APIRouter(prefix="/sql-assistant", tags=["sql-assistant"])


@router.post("/generate")
async def generate_sql(
    request: GenerateRequest,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        async for event in service.generate_sql_streaming(request):
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/validate", response_model=ValidationResponse)
async def validate_sql(
    request: ValidateRequest,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> ValidationResponse:
    return await service.validate_sql(request)


@router.post("/explain", response_model=ExplainResponse)
async def explain_sql(
    request: ExplainRequest,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> ExplainResponse:
    return await service.explain_sql(request)


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_sql(
    request: OptimizeRequest,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> OptimizeResponse:
    return await service.optimize_sql(request)


@router.get("/history", response_model=list[SqlGenerationHistoryItem])
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> list[SqlGenerationHistoryItem]:
    return await service.get_history(limit)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> SessionResponse:
    return await service.create_session(request)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> list[SessionResponse]:
    return await service.list_sessions()


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> SessionDetailResponse:
    return await service.get_session(session_id)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    service: SqlAssistantService = Depends(get_sql_assistant_service),
) -> None:
    await service.delete_session(session_id)
