from uuid import UUID

from fastapi import APIRouter, Depends, status

from dependencies import get_dashboard_service
from models.request.dashboard import (
    DashboardCreateRequest,
    DashboardUpdateRequest,
    WidgetCreateRequest,
    WidgetUpdateRequest,
)
from models.response.dashboard import (
    DashboardHtmlResponse,
    DashboardListItem,
    DashboardResponse,
    ShareResponse,
    WidgetResponse,
)
from services.dashboard import DashboardService

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    request: DashboardCreateRequest,
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    return await service.create(request)


@router.get("", response_model=list[DashboardListItem])
async def list_dashboards(
    service: DashboardService = Depends(get_dashboard_service),
) -> list[DashboardListItem]:
    return await service.list_dashboards()


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    return await service.get(dashboard_id)


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    request: DashboardUpdateRequest,
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    return await service.update(dashboard_id, request)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
) -> None:
    await service.delete(dashboard_id)


@router.post(
    "/{dashboard_id}/widgets",
    response_model=WidgetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_widget(
    dashboard_id: UUID,
    request: WidgetCreateRequest,
    service: DashboardService = Depends(get_dashboard_service),
) -> WidgetResponse:
    return await service.add_widget(dashboard_id, request)


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    request: WidgetUpdateRequest,
    service: DashboardService = Depends(get_dashboard_service),
) -> WidgetResponse:
    return await service.update_widget(dashboard_id, widget_id, request)


@router.delete(
    "/{dashboard_id}/widgets/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_widget(
    dashboard_id: UUID,
    widget_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
) -> None:
    await service.delete_widget(dashboard_id, widget_id)


@router.get("/{dashboard_id}/html", response_model=DashboardHtmlResponse)
async def get_dashboard_html(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardHtmlResponse:
    return await service.get_html(dashboard_id)


@router.post("/{dashboard_id}/share", response_model=ShareResponse)
async def share_dashboard(
    dashboard_id: UUID,
    service: DashboardService = Depends(get_dashboard_service),
) -> ShareResponse:
    return await service.share(dashboard_id)
