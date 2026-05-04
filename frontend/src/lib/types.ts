// ── Feature 1: Data Source ────────────────────────────────────────────────

export type DataSourceType = 'postgresql' | 'redshift' | 'trino' | 'mockup';
export type DataSourceStatus = 'connected' | 'disconnected' | 'error';

export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  description: string | null;
  config: Record<string, unknown>;
  status: DataSourceStatus;
  last_synced: string | null;
  created_at: string;
  updated_at: string;
}

export interface DataSourceCreate {
  name: string;
  type: DataSourceType;
  description?: string;
  config: Record<string, unknown>;
}

export interface DataSourceUpdate {
  name?: string;
  type?: DataSourceType;
  description?: string;
  config?: Record<string, unknown>;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
}

export interface SyncResult {
  data_source_id: string;
  message: string;
}

// ── Conversation Session ──────────────────────────────────────────────────

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  dataSources?: string[];
  createdAt: Date;
}

export interface Session {
  id: string;
  title: string;
  dataSourceId: string | null;
  createdAt: Date;
  messages: Message[];
}

/** @deprecated Use Message instead */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  timestamp: Date;
}

// ── Feature 2: Data Catalog — real backend types ──────────────────────────

export interface ApiColumn {
  id: string;
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  default_value: string | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  references_column: string | null;
  source_description: string | null;
  user_description: string | null;
  ordinal_position: number;
}

export interface ApiTable {
  id: string;
  schema_id: string;
  schema_name: string;
  table_name: string;
  table_type: 'table' | 'view';
  row_count: number;
  source_description: string | null;
  user_description: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface ApiTableDetail extends ApiTable {
  columns: ApiColumn[];
}

export interface ApiSchema {
  id: string;
  data_source_id: string;
  schema_name: string;
  table_count: number;
  created_at: string;
}

export interface ApiSourceCatalog {
  data_source_id: string;
  schemas: ApiSchema[];
  tables: ApiTable[];
}

export interface SemanticSearchFilters {
  schema_name?: string;
  table_types?: string[];
}

export interface SemanticSearchRequest {
  query: string;
  data_source_ids?: string[];
  search_type?: 'tables' | 'columns' | 'both';
  limit?: number;
  filters?: SemanticSearchFilters;
}

export interface SemanticSearchResultItem {
  type: 'table' | 'column';
  table_id: string | null;
  schema_name: string;
  table_name: string;
  column_name: string | null;
  description: string | null;
  relevance_score: number;
  snippet: string;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResultItem[];
  total_found: number;
  search_time_ms: number;
}

export interface CatalogRefreshResponse {
  data_source_id: string;
  message: string;
  schemas_synced: number;
  tables_synced: number;
  columns_synced: number;
}

// ── Feature 3: Text-to-SQL ────────────────────────────────────────────────

export interface GenerateSqlRequest {
  query: string;
  data_source_id?: string | null;
  session_id?: string | null;
  options?: {
    include_explanation?: boolean;
    sql_dialect?: 'postgresql' | 'mysql' | 'sqlite';
  };
}

export interface SqlChunkEvent {
  type: 'sql_chunk';
  content: string;
  generation_id: string;
}

export interface ValidationResult {
  is_valid: boolean;
  syntax_errors: string[];
  security_issues: string[];
  suggestions: string[];
}

export interface GenerationCompleteEvent {
  type: 'generation_complete';
  generation_id: string;
  sql: string | null;
  explanation: string | null;
  confidence_score: number | null;
  validation: ValidationResult;
}

export interface SseErrorEvent {
  type: 'error';
  message: string;
  generation_id: string | null;
}

export type SqlSseEvent = SqlChunkEvent | GenerationCompleteEvent | SseErrorEvent;

// ── Mock types (used for offline/mockup data source only) ────────────────

export interface CatalogColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string;
  description?: string;
}

export interface CatalogTable {
  name: string;
  type: 'table' | 'view';
  row_count: number;
  description: string;
  columns: CatalogColumn[];
  tags: string[];
}

export interface CatalogSchema {
  name: string;
  tables: CatalogTable[];
}

export interface DiscoveryResult {
  schema_name: string;
  table_name: string;
  column_name?: string;
  document_type: 'ddl' | 'doc' | 'example';
  title: string;
  snippet: string;
  relevance_score: number;
}

// ── Feature 3: SQL Assistant history ─────────────────────────────────────

export interface SqlGenerationHistoryItem {
  id: string;
  user_query: string;
  generated_sql: string | null;
  validation_status: string;
  confidence_score: number | null;
  llm_model: string | null;
  created_at: string;
}

// ── Feature 4: Data Analysis ──────────────────────────────────────────────

export interface ColumnInfo {
  name: string;
  type: string;
}

export interface ColumnStats {
  column_name: string;
  data_type: string;
  null_count: number;
  unique_count: number;
  total_count: number;
  min_value: string | null;
  max_value: string | null;
  avg_value: number | null;
  summary_stats: Record<string, unknown> | null;
}

export interface InsightItem {
  insight_type: string;
  insight_text: string;
  confidence_score: number | null;
}

export interface AnalysisOptions {
  include_statistics?: boolean;
  generate_insights?: boolean;
  limit_rows?: number;
}

export interface AnalysisExecuteRequest {
  sql: string;
  data_source_id: string;
  sql_generation_id?: string | null;
  options?: AnalysisOptions;
}

export interface AnalysisExecutionResponse {
  id: string;
  sql_generation_id: string | null;
  data_source_id: string | null;
  executed_sql: string;
  execution_time_ms: number | null;
  row_count: number | null;
  status: 'running' | 'completed' | 'failed';
  error_message: string | null;
  columns: ColumnInfo[];
  data: Record<string, unknown>[];
  statistics: ColumnStats[];
  insights: InsightItem[];
  visualizations: unknown[];
  workflow_id: string | null;
  created_at: string;
}

export interface AnalysisHistoryItem {
  id: string;
  sql_generation_id: string | null;
  data_source_id: string | null;
  executed_sql: string;
  execution_time_ms: number | null;
  row_count: number | null;
  status: string;
  error_message: string | null;
  created_at: string;
}

export interface ExportRequest {
  analysis_id: string;
  format: 'csv';
  include_metadata?: boolean;
}

export interface ExportResponse {
  analysis_id: string;
  format: string;
  download_url: string;
  expires_in_seconds: number;
}

// ── Feature 5: Dashboard ──────────────────────────────────────────────────

export interface DashboardCreateRequest {
  title: string;
  description?: string;
  layout?: 'grid' | 'free';
  is_public?: boolean;
  tags?: string[];
}

export interface DashboardUpdateRequest {
  title?: string;
  description?: string;
  layout?: 'grid' | 'free';
  is_public?: boolean;
  tags?: string[];
}

export interface WidgetCreateRequest {
  widget_type: 'chart' | 'table' | 'metric' | 'text';
  title: string;
  position_x?: number;
  position_y?: number;
  width?: number;
  height?: number;
  analysis_id?: string | null;
  chart_config?: Record<string, unknown> | null;
}

export interface WidgetResponse {
  id: string;
  dashboard_id: string;
  widget_type: 'chart' | 'table' | 'metric' | 'text';
  title: string;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  analysis_id: string | null;
  chart_config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardResponse {
  id: string;
  title: string;
  description: string | null;
  layout: string;
  is_public: boolean;
  tags: string[] | null;
  html_content: string | null;
  widgets: WidgetResponse[];
  created_at: string;
  updated_at: string;
}

export interface DashboardListItem {
  id: string;
  title: string;
  description: string | null;
  layout: string;
  is_public: boolean;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardHtmlResponse {
  dashboard_id: string;
  html: string;
}

export interface ShareResponse {
  dashboard_id: string;
  share_url: string;
  expires_in_seconds: number;
}
