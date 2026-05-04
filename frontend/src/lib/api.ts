import type {
  DataSource,
  DataSourceCreate,
  DataSourceUpdate,
  ConnectionTestResult,
  SyncResult,
  ApiSourceCatalog,
  ApiTableDetail,
  SemanticSearchRequest,
  SemanticSearchResponse,
  CatalogRefreshResponse,
  GenerateSqlRequest,
  SqlSseEvent,
  SqlGenerationHistoryItem,
  AnalysisExecuteRequest,
  AnalysisExecutionResponse,
  AnalysisHistoryItem,
  ExportRequest,
  ExportResponse,
  DashboardCreateRequest,
  DashboardUpdateRequest,
  DashboardListItem,
  DashboardResponse,
  WidgetCreateRequest,
  WidgetResponse,
  DashboardHtmlResponse,
  ShareResponse,
} from './types';

const BASE_URL =
  (import.meta.env.VITE_BACKEND_URL as string) ||
  window.location.origin.replace(':3000', ':8000') + '/api/v1';

// ── Error type ────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 204) return null as T;
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      detail = JSON.parse(text)?.detail ?? text;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return JSON.parse(text) as T;
}

const json = { 'Content-Type': 'application/json' };

// ── Feature 1: Data Source ────────────────────────────────────────────────

export const dataSourceApi = {
  list: (): Promise<DataSource[]> =>
    fetch(`${BASE_URL}/data-sources`).then(handle),

  get: (id: string): Promise<DataSource> =>
    fetch(`${BASE_URL}/data-sources/${id}`).then(handle),

  create: (data: DataSourceCreate): Promise<DataSource> =>
    fetch(`${BASE_URL}/data-sources`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(data),
    }).then(handle),

  update: (id: string, data: DataSourceUpdate): Promise<DataSource> =>
    fetch(`${BASE_URL}/data-sources/${id}`, {
      method: 'PUT',
      headers: json,
      body: JSON.stringify(data),
    }).then(handle),

  delete: (id: string): Promise<null> =>
    fetch(`${BASE_URL}/data-sources/${id}`, { method: 'DELETE' }).then(handle),

  testConnection: (id: string): Promise<ConnectionTestResult> =>
    fetch(`${BASE_URL}/data-sources/${id}/test`, { method: 'POST' }).then(handle),

  sync: (id: string): Promise<SyncResult> =>
    fetch(`${BASE_URL}/data-sources/${id}/sync`, { method: 'POST' }).then(handle),

  testConnectionDirect: (data: { type: string; config: Record<string, unknown> }): Promise<ConnectionTestResult> =>
    fetch(`${BASE_URL}/data-sources/test-connection`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(data),
    }).then(handle),
};

// ── Feature 2: Data Catalog ───────────────────────────────────────────────

export const dataCatalogApi = {
  getSourceCatalog: (dataSourceId: string): Promise<ApiSourceCatalog> =>
    fetch(`${BASE_URL}/data-catalog/sources/${dataSourceId}`).then(handle),

  getTableDetail: (tableId: string): Promise<ApiTableDetail> =>
    fetch(`${BASE_URL}/data-catalog/tables/${tableId}`).then(handle),

  semanticSearch: (req: SemanticSearchRequest): Promise<SemanticSearchResponse> =>
    fetch(`${BASE_URL}/data-catalog/semantic-search`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(req),
    }).then(handle),

  refresh: (dataSourceId: string): Promise<CatalogRefreshResponse> =>
    fetch(`${BASE_URL}/data-catalog/refresh`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify({ data_source_id: dataSourceId }),
    }).then(handle),
};

// ── Feature 3: SQL Assistant ──────────────────────────────────────────────

export const sqlAssistantApi = {
  async *generateSql(req: GenerateSqlRequest): AsyncGenerator<SqlSseEvent> {
    const res = await fetch(`${BASE_URL}/sql-assistant/generate`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const text = await res.text();
      let detail = text;
      try { detail = JSON.parse(text)?.detail ?? text; } catch {}
      throw new ApiError(res.status, detail);
    }
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';
      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith('data: ')) {
          try {
            yield JSON.parse(line.slice(6)) as SqlSseEvent;
          } catch {}
        }
      }
    }
  },

  getHistory: (limit = 50): Promise<SqlGenerationHistoryItem[]> =>
    fetch(`${BASE_URL}/sql-assistant/history?limit=${limit}`).then(handle),
};

// Keep legacy alias so ConversationView import still works
export const textToSqlApi = sqlAssistantApi;

// ── Feature 4: Data Analysis ──────────────────────────────────────────────

export const dataAnalysisApi = {
  execute: (req: AnalysisExecuteRequest): Promise<AnalysisExecutionResponse> =>
    fetch(`${BASE_URL}/data-analysis/execute`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(req),
    }).then(handle),

  getResult: (analysisId: string): Promise<AnalysisExecutionResponse> =>
    fetch(`${BASE_URL}/data-analysis/results/${analysisId}`).then(handle),

  getHistory: (limit = 50): Promise<AnalysisHistoryItem[]> =>
    fetch(`${BASE_URL}/data-analysis/history?limit=${limit}`).then(handle),

  exportResults: (req: ExportRequest): Promise<ExportResponse> =>
    fetch(`${BASE_URL}/data-analysis/export`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(req),
    }).then(handle),
};

// ── Feature 5: Dashboard ──────────────────────────────────────────────────

export const dashboardApi = {
  list: (): Promise<DashboardListItem[]> =>
    fetch(`${BASE_URL}/dashboards`).then(handle),

  get: (id: string): Promise<DashboardResponse> =>
    fetch(`${BASE_URL}/dashboards/${id}`).then(handle),

  create: (req: DashboardCreateRequest): Promise<DashboardResponse> =>
    fetch(`${BASE_URL}/dashboards`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(req),
    }).then(handle),

  update: (id: string, req: DashboardUpdateRequest): Promise<DashboardResponse> =>
    fetch(`${BASE_URL}/dashboards/${id}`, {
      method: 'PUT',
      headers: json,
      body: JSON.stringify(req),
    }).then(handle),

  delete: (id: string): Promise<null> =>
    fetch(`${BASE_URL}/dashboards/${id}`, { method: 'DELETE' }).then(handle),

  addWidget: (dashboardId: string, req: WidgetCreateRequest): Promise<WidgetResponse> =>
    fetch(`${BASE_URL}/dashboards/${dashboardId}/widgets`, {
      method: 'POST',
      headers: json,
      body: JSON.stringify(req),
    }).then(handle),

  deleteWidget: (dashboardId: string, widgetId: string): Promise<null> =>
    fetch(`${BASE_URL}/dashboards/${dashboardId}/widgets/${widgetId}`, {
      method: 'DELETE',
    }).then(handle),

  getHtml: (id: string): Promise<DashboardHtmlResponse> =>
    fetch(`${BASE_URL}/dashboards/${id}/html`).then(handle),

  share: (id: string): Promise<ShareResponse> =>
    fetch(`${BASE_URL}/dashboards/${id}/share`, { method: 'POST' }).then(handle),
};
