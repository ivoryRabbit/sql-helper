import logging
from uuid import UUID

from fastapi import HTTPException

from clients.storage import StorageClient
from models.entities import Dashboard, DashboardWidget
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
from repositories.dashboard import DashboardRepository, DashboardWidgetRepository

logger = logging.getLogger(__name__)

_DASHBOARD_BUCKET = "dashboards"
_DASHBOARD_CSS = """
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
.dashboard-container { padding: 20px; }
.dashboard-header { background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,.1); }
.dashboard-header h1 { margin: 0 0 8px; color: #333; }
.dashboard-header p { margin: 0; color: #666; }
.widgets-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; }
.widget { background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,.1); overflow: hidden; }
.widget-header { padding: 12px 16px; border-bottom: 1px solid #eee; background: #fafafa; }
.widget-header h3 { margin: 0; font-size: 15px; color: #333; }
.widget-content { padding: 16px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 8px; text-align: left; border-bottom: 1px solid #eee; }
.data-table th { background: #f8f9fa; font-weight: 600; }
.metric-value { font-size: 48px; font-weight: 700; color: #2196F3; text-align: center; padding: 24px 0; }
.text-content { line-height: 1.6; color: #444; }
"""


class DashboardService:
    def __init__(
        self,
        dashboard_repo: DashboardRepository,
        widget_repo: DashboardWidgetRepository,
        storage: StorageClient,
    ) -> None:
        self._dashboard_repo = dashboard_repo
        self._widget_repo = widget_repo
        self._storage = storage

    # ── Dashboard CRUD ────────────────────────────────────────────────────────

    async def create(self, request: DashboardCreateRequest) -> DashboardResponse:
        dashboard = await self._dashboard_repo.create(
            title=request.title,
            description=request.description,
            layout=request.layout,
            is_public=request.is_public,
            tags=request.tags,
        )
        return self._to_response(dashboard, [])

    async def list_dashboards(self) -> list[DashboardListItem]:
        dashboards = await self._dashboard_repo.list_all()
        return [DashboardListItem.model_validate(d) for d in dashboards]

    async def get(self, dashboard_id: UUID) -> DashboardResponse:
        dashboard = await self._require_dashboard(dashboard_id)
        widgets = await self._dashboard_repo.get_widgets(dashboard_id)
        return self._to_response(dashboard, widgets)

    async def update(self, dashboard_id: UUID, request: DashboardUpdateRequest) -> DashboardResponse:
        dashboard = await self._require_dashboard(dashboard_id)
        updates = request.model_dump(exclude_none=True)
        if updates:
            dashboard = await self._dashboard_repo.update(dashboard_id, **updates)
        widgets = await self._dashboard_repo.get_widgets(dashboard_id)
        return self._to_response(dashboard, widgets)

    async def delete(self, dashboard_id: UUID) -> None:
        await self._require_dashboard(dashboard_id)
        await self._dashboard_repo.delete(dashboard_id)

    # ── Widget CRUD ───────────────────────────────────────────────────────────

    async def add_widget(self, dashboard_id: UUID, request: WidgetCreateRequest) -> WidgetResponse:
        await self._require_dashboard(dashboard_id)
        widget = await self._widget_repo.create(
            dashboard_id=dashboard_id,
            widget_type=request.widget_type,
            title=request.title,
            position_x=request.position_x,
            position_y=request.position_y,
            width=request.width,
            height=request.height,
            analysis_id=request.analysis_id,
            chart_config=request.chart_config,
        )
        return WidgetResponse.model_validate(widget)

    async def update_widget(
        self, dashboard_id: UUID, widget_id: UUID, request: WidgetUpdateRequest
    ) -> WidgetResponse:
        widget = await self._require_widget(dashboard_id, widget_id)
        updates = request.model_dump(exclude_none=True)
        if updates:
            widget = await self._widget_repo.update(widget_id, **updates)
        return WidgetResponse.model_validate(widget)

    async def delete_widget(self, dashboard_id: UUID, widget_id: UUID) -> None:
        await self._require_widget(dashboard_id, widget_id)
        await self._widget_repo.delete(widget_id)

    # ── HTML rendering ────────────────────────────────────────────────────────

    async def get_html(self, dashboard_id: UUID) -> DashboardHtmlResponse:
        dashboard = await self._require_dashboard(dashboard_id)
        widgets = await self._dashboard_repo.get_widgets(dashboard_id)
        html = _render_html(dashboard, widgets)

        # Persist rendered HTML and store back to DB for caching
        await self._dashboard_repo.update(dashboard_id, html_content=html)

        return DashboardHtmlResponse(dashboard_id=dashboard_id, html=html)

    # ── Sharing ───────────────────────────────────────────────────────────────

    async def share(self, dashboard_id: UUID) -> ShareResponse:
        dashboard = await self._require_dashboard(dashboard_id)
        widgets = await self._dashboard_repo.get_widgets(dashboard_id)
        html = _render_html(dashboard, widgets)
        content = html.encode("utf-8")

        await self._storage.create_bucket_if_not_exists(_DASHBOARD_BUCKET)
        key = f"{dashboard_id}.html"
        await self._storage.upload(_DASHBOARD_BUCKET, key, content, content_type="text/html")
        url = await self._storage.presigned_url(_DASHBOARD_BUCKET, key, expires_seconds=3600)

        logger.info("Dashboard shared: dashboard_id=%s url=%s", dashboard_id, url)
        return ShareResponse(dashboard_id=dashboard_id, share_url=url, expires_in_seconds=3600)

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _require_dashboard(self, dashboard_id: UUID) -> Dashboard:
        dashboard = await self._dashboard_repo.get(dashboard_id)
        if dashboard is None:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return dashboard

    async def _require_widget(self, dashboard_id: UUID, widget_id: UUID) -> DashboardWidget:
        widget = await self._widget_repo.get(widget_id)
        if widget is None or widget.dashboard_id != dashboard_id:
            raise HTTPException(status_code=404, detail="Widget not found")
        return widget

    @staticmethod
    def _to_response(dashboard: Dashboard, widgets: list[DashboardWidget]) -> DashboardResponse:
        return DashboardResponse(
            id=dashboard.id,
            title=dashboard.title,
            description=dashboard.description,
            layout=dashboard.layout,
            is_public=dashboard.is_public,
            tags=dashboard.tags,
            html_content=dashboard.html_content,
            widgets=[WidgetResponse.model_validate(w) for w in widgets],
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
        )


# ── HTML renderer (pure function, no I/O) ────────────────────────────────────

def _render_html(dashboard: Dashboard, widgets: list[DashboardWidget]) -> str:
    widgets_html = "\n".join(_render_widget(w) for w in widgets)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_esc(dashboard.title)}</title>
  <style>{_DASHBOARD_CSS}</style>
</head>
<body>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1>{_esc(dashboard.title)}</h1>
      {f'<p>{_esc(dashboard.description)}</p>' if dashboard.description else ''}
    </div>
    <div class="widgets-grid">
      {widgets_html}
    </div>
  </div>
</body>
</html>"""


def _render_widget(widget: DashboardWidget) -> str:
    col_span = min(widget.width, 12)
    body = _render_widget_body(widget)
    return f"""<div class="widget" style="grid-column: span {col_span};">
  <div class="widget-header"><h3>{_esc(widget.title)}</h3></div>
  <div class="widget-content">{body}</div>
</div>"""


def _render_widget_body(widget: DashboardWidget) -> str:
    if widget.widget_type == "chart":
        return f'<canvas id="chart-{widget.id}" style="max-height:300px;"></canvas>'
    if widget.widget_type == "table":
        return f'<div id="table-{widget.id}"><em>Table data loaded at runtime.</em></div>'
    if widget.widget_type == "metric":
        return f'<div class="metric-value" id="metric-{widget.id}">—</div>'
    # text widget
    content = (widget.chart_config or {}).get("content", "")
    return f'<div class="text-content">{_esc(content)}</div>'


def _esc(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )
