from uuid import UUID

from fastapi import APIRouter, Depends, Query

from dependencies import get_data_analysis_service
from models.request.data_analysis import AnalysisExecuteRequest, DataExportRequest
from models.response.data_analysis import (
    AnalysisExecutionResponse,
    AnalysisHistoryItem,
    ExportResponse,
)
from services.data_analysis import DataAnalysisService

router = APIRouter(prefix="/data-analysis", tags=["data-analysis"])


@router.post("/execute", response_model=AnalysisExecutionResponse, status_code=201)
async def execute_analysis(
    request: AnalysisExecuteRequest,
    service: DataAnalysisService = Depends(get_data_analysis_service),
) -> AnalysisExecutionResponse:
    return await service.execute(request)


@router.get("/results/{analysis_id}", response_model=AnalysisExecutionResponse)
async def get_result(
    analysis_id: UUID,
    service: DataAnalysisService = Depends(get_data_analysis_service),
) -> AnalysisExecutionResponse:
    return await service.get_result(analysis_id)


@router.get("/history", response_model=list[AnalysisHistoryItem])
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    service: DataAnalysisService = Depends(get_data_analysis_service),
) -> list[AnalysisHistoryItem]:
    return await service.get_history(limit)


@router.post("/export", response_model=ExportResponse)
async def export_results(
    request: DataExportRequest,
    service: DataAnalysisService = Depends(get_data_analysis_service),
) -> ExportResponse:
    return await service.export(request)
