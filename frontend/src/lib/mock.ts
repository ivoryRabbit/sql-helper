import type {
  CatalogSchema,
  DataSource,
  DiscoveryResult,
} from './types';

// ── Mockup Data Source ────────────────────────────────────────────────────
// Auto-injected when the API server is unreachable. Frontend-only — never sent to backend.

export const MOCK_DATA_SOURCE: DataSource = {
  id: '__mockup__',
  name: 'Sample DB (Mockup)',
  type: 'mockup',
  description: '백엔드 없이 프론트엔드를 테스트하기 위한 샘플 데이터 소스입니다.',
  config: {},
  status: 'connected',
  last_synced: new Date().toISOString(),
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

// ── Feature 2: Data Catalog ───────────────────────────────────────────────

export const mockCatalog: CatalogSchema[] = [
  {
    name: 'public',
    tables: [
      {
        name: 'orders',
        type: 'table',
        row_count: 125430,
        description: '고객 주문 데이터',
        tags: ['거래', '매출'],
        columns: [
          { name: 'id', type: 'UUID', nullable: false, primary_key: true },
          { name: 'user_id', type: 'UUID', nullable: false, primary_key: false, foreign_key: 'users.id' },
          { name: 'amount', type: 'DECIMAL(12,2)', nullable: false, primary_key: false },
          { name: 'status', type: 'VARCHAR(20)', nullable: false, primary_key: false },
          { name: 'created_at', type: 'TIMESTAMPTZ', nullable: false, primary_key: false },
        ],
      },
      {
        name: 'users',
        type: 'table',
        row_count: 48210,
        description: '서비스 가입 고객 정보',
        tags: ['고객', '회원'],
        columns: [
          { name: 'id', type: 'UUID', nullable: false, primary_key: true },
          { name: 'email', type: 'VARCHAR(255)', nullable: false, primary_key: false },
          { name: 'name', type: 'VARCHAR(100)', nullable: true, primary_key: false },
          { name: 'tier', type: 'VARCHAR(20)', nullable: false, primary_key: false, description: 'free | pro | enterprise' },
          { name: 'created_at', type: 'TIMESTAMPTZ', nullable: false, primary_key: false },
        ],
      },
      {
        name: 'products',
        type: 'table',
        row_count: 3200,
        description: '상품 카탈로그',
        tags: ['상품', '재고'],
        columns: [
          { name: 'id', type: 'UUID', nullable: false, primary_key: true },
          { name: 'name', type: 'VARCHAR(255)', nullable: false, primary_key: false },
          { name: 'category', type: 'VARCHAR(100)', nullable: true, primary_key: false },
          { name: 'price', type: 'DECIMAL(10,2)', nullable: false, primary_key: false },
          { name: 'stock', type: 'INTEGER', nullable: false, primary_key: false },
        ],
      },
      {
        name: 'monthly_revenue',
        type: 'view',
        row_count: 36,
        description: '월별 매출 집계 뷰',
        tags: ['매출', '집계'],
        columns: [
          { name: 'month', type: 'DATE', nullable: false, primary_key: false },
          { name: 'total_revenue', type: 'DECIMAL', nullable: true, primary_key: false },
          { name: 'order_count', type: 'BIGINT', nullable: true, primary_key: false },
        ],
      },
    ],
  },
  {
    name: 'analytics',
    tables: [
      {
        name: 'events',
        type: 'table',
        row_count: 4820000,
        description: '사용자 행동 이벤트 로그',
        tags: ['이벤트', '분석'],
        columns: [
          { name: 'id', type: 'UUID', nullable: false, primary_key: true },
          { name: 'user_id', type: 'UUID', nullable: true, primary_key: false },
          { name: 'event_type', type: 'VARCHAR(100)', nullable: false, primary_key: false },
          { name: 'properties', type: 'JSONB', nullable: true, primary_key: false },
          { name: 'occurred_at', type: 'TIMESTAMPTZ', nullable: false, primary_key: false },
        ],
      },
      {
        name: 'funnel_summary',
        type: 'view',
        row_count: 90,
        description: '전환 퍼널 요약',
        tags: ['퍼널', '전환'],
        columns: [
          { name: 'date', type: 'DATE', nullable: false, primary_key: false },
          { name: 'step', type: 'VARCHAR(50)', nullable: false, primary_key: false },
          { name: 'user_count', type: 'BIGINT', nullable: true, primary_key: false },
          { name: 'conversion_rate', type: 'FLOAT', nullable: true, primary_key: false },
        ],
      },
    ],
  },
];

// ── Feature 3: Data Discovery ─────────────────────────────────────────────

export const mockDiscoveryResults: DiscoveryResult[] = [
  {
    schema_name: 'public',
    table_name: 'orders',
    document_type: 'ddl',
    title: 'orders — 고객 주문 테이블',
    snippet: 'id, user_id (→ users), amount DECIMAL(12,2), status VARCHAR(20), created_at TIMESTAMPTZ',
    relevance_score: 0.94,
  },
  {
    schema_name: 'public',
    table_name: 'monthly_revenue',
    document_type: 'doc',
    title: 'monthly_revenue — 월별 매출 집계',
    snippet: '매월 주문 금액을 집계한 VIEW. 대시보드 매출 위젯에서 사용.',
    relevance_score: 0.87,
  },
  {
    schema_name: 'analytics',
    table_name: 'events',
    document_type: 'ddl',
    title: 'events — 사용자 행동 이벤트',
    snippet: 'event_type, properties JSONB, occurred_at TIMESTAMPTZ. 4.8M rows.',
    relevance_score: 0.72,
  },
  {
    schema_name: 'public',
    table_name: 'users',
    column_name: 'tier',
    document_type: 'doc',
    title: 'users.tier — 고객 등급',
    snippet: "고객 구독 등급. 값: 'free' | 'pro' | 'enterprise'",
    relevance_score: 0.65,
  },
  {
    schema_name: 'analytics',
    table_name: 'funnel_summary',
    document_type: 'example',
    title: '퍼널 전환율 조회 예시',
    snippet: "SELECT step, AVG(conversion_rate) FROM funnel_summary WHERE date >= '2024-01-01' GROUP BY step",
    relevance_score: 0.58,
  },
];
