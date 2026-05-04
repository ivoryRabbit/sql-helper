import { writable, derived } from 'svelte/store';

export type Language = 'en' | 'ko';

function detectBrowserLanguage(): Language {
  const lang = (navigator.language || '').toLowerCase();
  if (lang.startsWith('ko')) return 'ko';
  return 'en';
}

export const language = writable<Language>(detectBrowserLanguage());

type Translations = Record<string, string>;

const en: Translations = {
  // Common
  'common.loading': 'Loading...',
  'common.cancel': 'Cancel',
  'common.save': 'Save',
  'common.saving': 'Saving…',
  'common.delete': 'Delete',
  'common.retry': 'Retry',
  'common.copy': 'Copy',
  'common.copied': 'Copied ✓',
  'common.optional': 'Optional',
  'common.refresh': 'Refresh',
  'common.close': 'Close',

  // App.svelte
  'app.noSources.title': 'No data sources registered',
  'app.noSources.hint': 'Register a database connection to use SQL Assistant.',
  'app.noSources.cta': 'Register Data Source →',
  'app.noTabs.title': 'Select a connection to start a conversation',
  'app.noTabs.hint': 'Select a database connection from the SQL Assistant sidebar.',

  // AppBar.svelte
  'appbar.home.title': 'Home (Refresh)',

  // NavSidebar.svelte
  'nav.expand': 'Expand sidebar',
  'nav.collapse': 'Collapse sidebar',
  'nav.noConnections': 'No connections registered',

  // EmptyDataSource.svelte
  'empty.noSources.title': 'No data sources registered',
  'empty.noSources.desc': 'Register a database connection to use this feature.',
  'empty.noSources.cta': 'Register Data Source →',
  'empty.noSelect.title': 'Select a data source',
  'empty.noSelect.desc': 'Select a data source to work with from the selector above.',

  // ConversationView.svelte
  'conv.error.sse': 'An error occurred: {message}',
  'conv.error.request': 'Failed to process request: {message}',

  // PromptInputBar.svelte
  'prompt.placeholder': 'Ask a question about your data... (Enter to send, Shift+Enter for newline)',

  // SessionPanel.svelte
  'session.delete.label': 'Delete session',

  // stores.ts
  'session.greeting.source': 'Hello! Ask me anything about {name}.',
  'session.greeting.default': 'Hello! Starting a new conversation.',

  // DataSource.svelte
  'ds.title': 'Data Sources',
  'ds.subtitle': 'Register and manage database connections.',
  'ds.btn.new': '+ New Data Source',
  'ds.form.title': 'Register Data Source',
  'ds.field.name': 'Name *',
  'ds.field.type': 'Type *',
  'ds.field.desc': 'Description',
  'ds.mockup.option': 'Mockup (for testing)',
  'ds.mockup.notice': '🧪 Mockup source is a virtual data source for testing the frontend UI without a backend.',
  'ds.btn.test': 'Test Connection',
  'ds.btn.testing': 'Testing…',
  'ds.error.name': 'Please enter a name',
  'ds.confirm.delete': "Are you sure you want to delete '{name}'?",
  'ds.status.connected': 'Connected',
  'ds.status.disconnected': 'Disconnected',
  'ds.status.error': 'Error',
  'ds.loading': 'Loading…',
  'ds.empty.text': 'No data sources registered.',
  'ds.empty.cta': 'Register First Data Source',
  'ds.card.lastSynced': 'Last synced:',
  'ds.card.mockInfo': 'Test source — no connection needed',
  'ds.card.testing': 'Testing…',
  'ds.card.syncing': 'Syncing…',
  'ds.card.syncCatalog': 'Sync Catalog',
  'ds.card.delete': 'Delete',

  // DataCatalog.svelte
  'catalog.title': 'Data Catalog',
  'catalog.subtitle': 'Browse schemas or search for relevant tables using natural language.',
  'catalog.btn.syncing': 'Syncing…',
  'catalog.btn.sync': 'Sync Catalog',
  'catalog.refresh.msg': '{message} (schemas: {schemas}, tables: {tables}, columns: {columns})',
  'catalog.browse.placeholder': 'Filter by table, description, or tag…',
  'catalog.loading': 'Loading catalog…',
  'catalog.empty.text': 'No catalog data found.',
  'catalog.empty.hint': "Click 'Sync Catalog' to fetch schemas.",
  'catalog.noResults': 'No results found.',
  'catalog.detail.loading': 'Loading column info…',
  'catalog.detail.empty': 'Select a table from the left.',
  'catalog.search.placeholder': 'e.g. monthly sales aggregate, customer tier, event log…',
  'catalog.search.btn.searching': 'Searching…',
  'catalog.search.btn': 'Search',
  'catalog.search.loading': 'Running vector similarity search…',
  'catalog.search.count': '{count} results',
  'catalog.search.hint': 'By relevance · {ms}ms',
  'catalog.search.noResults': 'No relevant tables or columns found.',
  'catalog.search.empty': 'Enter a query to find relevant tables and columns using vector similarity search.',
  'catalog.type.table': 'Table',
  'catalog.type.column': 'Column',

  // DataAnalysis.svelte
  'analysis.title': 'Data Analysis',
  'analysis.subtitle': 'Execute SQL and analyze results with statistics.',
  'analysis.history.header': 'Execution History ({count})',
  'analysis.history.loading': 'Loading...',
  'analysis.history.empty': 'No execution history yet.',
  'analysis.editor.placeholder': 'SELECT * FROM schema.table LIMIT 100\n\n⌘+Enter or Ctrl+Enter to run',
  'analysis.btn.running': 'Running...',
  'analysis.btn.run': '▶ Run',
  'analysis.export.generating': 'Generating...',
  'analysis.export.csv': 'Export CSV',
  'analysis.running.msg': 'Analysis is running. Results will appear automatically when complete...',
  'analysis.error.default': 'An error occurred during execution.',
  'analysis.tab.data': 'Data Table',
  'analysis.tab.stats': 'Column Stats ({count})',
  'analysis.tab.insights': 'Insights ({count})',
  'analysis.data.empty': 'No results.',
  'analysis.stats.total': 'Total',
  'analysis.stats.unique': 'Unique',
  'analysis.stats.min': 'Min',
  'analysis.stats.max': 'Max',
  'analysis.stats.avg': 'Avg',
  'analysis.stats.empty': 'No statistics available.',
  'analysis.insights.empty': 'No insights available.',
  'analysis.placeholder': 'Enter SQL and click Run or press ⌘ Enter to start analysis.',

  // Dashboard.svelte
  'dash.title': 'Dashboard',
  'dash.subtitle': 'Create and manage dashboards from data analysis results.',
  'dash.btn.new': '+ New Dashboard',
  'dash.confirm.delete': 'Are you sure you want to delete the "{title}" dashboard?',
  'dash.form.title': 'Create New Dashboard',
  'dash.form.field.title': 'Title *',
  'dash.form.placeholder.title': 'Dashboard title',
  'dash.form.field.desc': 'Description',
  'dash.form.field.tags': 'Tags (comma separated)',
  'dash.form.placeholder.tags': 'e.g. sales, customer, analytics',
  'dash.form.field.visibility': 'Visibility',
  'dash.form.public': 'Public',
  'dash.form.private': 'Private',
  'dash.btn.creating': 'Creating...',
  'dash.btn.create': 'Create Dashboard',
  'dash.loading': 'Loading...',
  'dash.empty.text': 'No dashboards yet.',
  'dash.empty.hint': "Create your first dashboard using the '+ New Dashboard' button.",
  'dash.badge.public': 'Public',
  'dash.badge.private': 'Private',
  'dash.back': '← Back to list',
  'dash.btn.togglePublic': '🔓 Public',
  'dash.btn.togglePrivate': '🔒 Private',
  'dash.btn.htmlPreview': 'HTML Preview',
  'dash.btn.processing': 'Processing...',
  'dash.btn.share': 'Share Link',
  'dash.btn.deleting': 'Deleting...',
  'dash.btn.delete': 'Delete',
  'dash.widgets.header': 'Widgets ({count})',
  'dash.widgets.add': '+ Add Widget',
  'dash.widget.type': 'Widget Type',
  'dash.widget.chart': '📈 Chart',
  'dash.widget.table': '📋 Table',
  'dash.widget.metric': '🔢 Metric',
  'dash.widget.text': '📝 Text',
  'dash.widget.titleLabel': 'Widget Title',
  'dash.widget.analysis': 'Link Analysis Result',
  'dash.widget.none': '— None —',
  'dash.widget.adding': 'Adding...',
  'dash.widget.add': 'Add',
  'dash.widgets.empty': 'No widgets. Add one using the button above.',
  'dash.share.label': 'Share URL:',
  'dash.share.copy': 'Copy',
  'dash.html.header': 'HTML Preview',
  'dash.html.close': '✕ Close',
  'dash.metric.rows': 'Rows',
  'dash.metric.columns': 'Columns',
  'dash.chart.noData': 'Not enough data to render a chart.',
  'dash.widget.noData': 'No analysis result linked.',

  // TextToSQL.svelte
  'sql.title': 'SQL Generation',
  'sql.subtitle': 'View SQL history generated from natural language questions.',
  'sql.hint': '💬 Generate new SQL from the chat on the right.',
  'sql.history.header': 'Recent Generation History ({count})',
  'sql.history.loading': 'Loading...',
  'sql.history.empty': 'No generation history.\nEnter a question in the chat on the right.',
  'sql.detail.question': 'Question',
  'sql.detail.generatedSql': 'Generated SQL',
  'sql.detail.copy': 'Copy',
  'sql.detail.copied': 'Copied ✓',
  'sql.detail.noSql': 'No SQL was generated.',
  'sql.detail.confidence': 'Confidence:',
  'sql.detail.validation': 'Validation:',
  'sql.detail.model': 'Model:',
  'sql.detail.createdAt': 'Created at:',
  'sql.empty': 'Select a history item on the left or enter a question in the chat on the right.',
};

const ko: Translations = {
  // Common
  'common.loading': '로딩 중...',
  'common.cancel': '취소',
  'common.save': '저장',
  'common.saving': '저장 중…',
  'common.delete': '삭제',
  'common.retry': '재시도',
  'common.copy': '복사',
  'common.copied': '복사됨 ✓',
  'common.optional': '선택 사항',
  'common.refresh': '새로고침',
  'common.close': '닫기',

  // App.svelte
  'app.noSources.title': '등록된 데이터 소스가 없습니다',
  'app.noSources.hint': 'SQL 어시스턴트를 사용하려면 먼저 데이터베이스 연결을 등록해야 합니다.',
  'app.noSources.cta': '데이터 소스 등록하기 →',
  'app.noTabs.title': '커넥션을 선택하면 대화가 시작됩니다',
  'app.noTabs.hint': '좌측 SQL Assistant에서 데이터베이스 커넥션을 선택하세요.',

  // AppBar.svelte
  'appbar.home.title': '홈으로 (새로고침)',

  // NavSidebar.svelte
  'nav.expand': '사이드바 펼치기',
  'nav.collapse': '사이드바 접기',
  'nav.noConnections': '등록된 커넥션 없음',

  // EmptyDataSource.svelte
  'empty.noSources.title': '등록된 데이터 소스가 없습니다',
  'empty.noSources.desc': '이 기능을 사용하려면 먼저 데이터베이스 연결을 등록해야 합니다.',
  'empty.noSources.cta': '데이터 소스 등록하기 →',
  'empty.noSelect.title': '데이터 소스를 선택하세요',
  'empty.noSelect.desc': '상단 셀렉터에서 작업할 데이터 소스를 선택해 주세요.',

  // ConversationView.svelte
  'conv.error.sse': '오류가 발생했습니다: {message}',
  'conv.error.request': '요청 처리 중 오류가 발생했습니다: {message}',

  // PromptInputBar.svelte
  'prompt.placeholder': '데이터에 대해 질문하세요...  (Enter 전송, Shift+Enter 줄바꿈)',

  // SessionPanel.svelte
  'session.delete.label': '세션 삭제',

  // stores.ts
  'session.greeting.source': '안녕하세요! {name}에 대해 궁금한 것을 질문해 주세요.',
  'session.greeting.default': '안녕하세요! 새 대화를 시작합니다.',

  // DataSource.svelte
  'ds.title': '데이터 소스',
  'ds.subtitle': '데이터베이스 연결을 등록하고 관리합니다.',
  'ds.btn.new': '+ 새 데이터 소스',
  'ds.form.title': '데이터 소스 등록',
  'ds.field.name': '이름 *',
  'ds.field.type': '타입 *',
  'ds.field.desc': '설명',
  'ds.mockup.option': 'Mockup (테스트용)',
  'ds.mockup.notice': '🧪 Mockup 소스는 백엔드 없이 프론트엔드 UI를 테스트할 수 있는 가상 데이터 소스입니다.',
  'ds.btn.test': '연결 테스트',
  'ds.btn.testing': '테스트 중…',
  'ds.error.name': '이름을 입력하세요',
  'ds.confirm.delete': "'{name}' 데이터 소스를 삭제하시겠습니까?",
  'ds.status.connected': '연결됨',
  'ds.status.disconnected': '미연결',
  'ds.status.error': '오류',
  'ds.loading': '불러오는 중…',
  'ds.empty.text': '등록된 데이터 소스가 없습니다.',
  'ds.empty.cta': '첫 데이터 소스 등록',
  'ds.card.lastSynced': '마지막 동기화:',
  'ds.card.mockInfo': '테스트용 소스 — 연결 불필요',
  'ds.card.testing': '테스트 중…',
  'ds.card.syncing': '동기화 중…',
  'ds.card.syncCatalog': '카탈로그 동기화',
  'ds.card.delete': '삭제',

  // DataCatalog.svelte
  'catalog.title': '데이터 카탈로그',
  'catalog.subtitle': '스키마를 탐색하거나 자연어로 관련 테이블을 검색합니다.',
  'catalog.btn.syncing': '동기화 중…',
  'catalog.btn.sync': '카탈로그 동기화',
  'catalog.refresh.msg': '{message} (스키마 {schemas}, 테이블 {tables}, 컬럼 {columns})',
  'catalog.browse.placeholder': '테이블·설명·태그 필터…',
  'catalog.loading': '카탈로그 로딩 중…',
  'catalog.empty.text': '카탈로그 데이터가 없습니다.',
  'catalog.empty.hint': '"카탈로그 동기화" 버튼을 눌러 스키마를 가져오세요.',
  'catalog.noResults': '검색 결과가 없습니다.',
  'catalog.detail.loading': '컬럼 정보 로딩 중…',
  'catalog.detail.empty': '왼쪽에서 테이블을 선택하세요.',
  'catalog.search.placeholder': '예: 월별 매출 집계, 고객 등급, 이벤트 로그…',
  'catalog.search.btn.searching': '검색 중…',
  'catalog.search.btn': '검색',
  'catalog.search.loading': '벡터 유사도 검색 중…',
  'catalog.search.count': '{count}개 결과',
  'catalog.search.hint': '관련도 순 · {ms}ms',
  'catalog.search.noResults': '관련 테이블/컬럼을 찾지 못했습니다.',
  'catalog.search.empty': '검색어를 입력하면 벡터 유사도 기반으로 관련 테이블·컬럼을 찾아드립니다.',
  'catalog.type.table': '테이블',
  'catalog.type.column': '컬럼',

  // DataAnalysis.svelte
  'analysis.title': '데이터 분석',
  'analysis.subtitle': 'SQL을 실행하고 결과를 통계와 함께 분석합니다.',
  'analysis.history.header': '실행 이력 ({count})',
  'analysis.history.loading': '로딩 중...',
  'analysis.history.empty': '아직 실행 이력이 없습니다.',
  'analysis.editor.placeholder': 'SELECT * FROM schema.table LIMIT 100\n\n⌘+Enter 또는 Ctrl+Enter로 실행',
  'analysis.btn.running': '실행 중...',
  'analysis.btn.run': '▶ 실행',
  'analysis.export.generating': '생성 중...',
  'analysis.export.csv': 'CSV 내보내기',
  'analysis.running.msg': '분석 실행 중입니다. 완료되면 자동으로 결과가 표시됩니다...',
  'analysis.error.default': '실행 중 오류가 발생했습니다.',
  'analysis.tab.data': '데이터 테이블',
  'analysis.tab.stats': '컬럼 통계 ({count})',
  'analysis.tab.insights': '인사이트 ({count})',
  'analysis.data.empty': '결과가 없습니다.',
  'analysis.stats.total': '전체',
  'analysis.stats.unique': '고유값',
  'analysis.stats.min': '최솟값',
  'analysis.stats.max': '최댓값',
  'analysis.stats.avg': '평균',
  'analysis.stats.empty': '통계 데이터가 없습니다.',
  'analysis.insights.empty': '인사이트가 없습니다.',
  'analysis.placeholder': 'SQL을 입력하고 실행 버튼을 클릭하거나 ⌘ Enter를 눌러 분석을 시작하세요.',

  // Dashboard.svelte
  'dash.title': '대시보드',
  'dash.subtitle': '데이터 분석 결과로 대시보드를 만들고 관리합니다.',
  'dash.btn.new': '+ 새 대시보드',
  'dash.confirm.delete': '"{title}" 대시보드를 삭제하시겠습니까?',
  'dash.form.title': '새 대시보드 만들기',
  'dash.form.field.title': '제목 *',
  'dash.form.placeholder.title': '대시보드 제목',
  'dash.form.field.desc': '설명',
  'dash.form.field.tags': '태그 (쉼표 구분)',
  'dash.form.placeholder.tags': '예: 매출, 고객, 분석',
  'dash.form.field.visibility': '공개 여부',
  'dash.form.public': '공개',
  'dash.form.private': '비공개',
  'dash.btn.creating': '생성 중...',
  'dash.btn.create': '대시보드 만들기',
  'dash.loading': '로딩 중...',
  'dash.empty.text': '대시보드가 없습니다.',
  'dash.empty.hint': "'새 대시보드' 버튼으로 첫 대시보드를 만들어보세요.",
  'dash.badge.public': '공개',
  'dash.badge.private': '비공개',
  'dash.back': '← 목록으로',
  'dash.btn.togglePublic': '🔓 공개',
  'dash.btn.togglePrivate': '🔒 비공개',
  'dash.btn.htmlPreview': 'HTML 미리보기',
  'dash.btn.processing': '처리 중...',
  'dash.btn.share': '공유 링크',
  'dash.btn.deleting': '삭제 중...',
  'dash.btn.delete': '삭제',
  'dash.widgets.header': '위젯 ({count})',
  'dash.widgets.add': '+ 위젯 추가',
  'dash.widget.type': '위젯 유형',
  'dash.widget.chart': '📈 차트',
  'dash.widget.table': '📋 테이블',
  'dash.widget.metric': '🔢 지표',
  'dash.widget.text': '📝 텍스트',
  'dash.widget.titleLabel': '위젯 제목',
  'dash.widget.analysis': '연결할 분석 결과',
  'dash.widget.none': '— 선택 안 함 —',
  'dash.widget.adding': '추가 중...',
  'dash.widget.add': '추가',
  'dash.widgets.empty': '위젯이 없습니다. 위의 버튼으로 추가하세요.',
  'dash.share.label': '공유 URL:',
  'dash.share.copy': '복사',
  'dash.html.header': 'HTML 미리보기',
  'dash.html.close': '✕ 닫기',
  'dash.metric.rows': '행 수',
  'dash.metric.columns': '컬럼 수',
  'dash.chart.noData': '차트를 그리기에 데이터가 부족합니다.',
  'dash.widget.noData': '분석 결과가 연결되지 않았습니다.',

  // TextToSQL.svelte
  'sql.title': 'SQL 생성',
  'sql.subtitle': '자연어 질문에서 생성된 SQL 이력을 확인합니다.',
  'sql.hint': '💬 오른쪽 채팅에서 새 SQL을 생성해보세요.',
  'sql.history.header': '최근 생성 이력 ({count})',
  'sql.history.loading': '로딩 중...',
  'sql.history.empty': '생성 이력이 없습니다.\n오른쪽 채팅에서 질문을 입력해보세요.',
  'sql.detail.question': '질문',
  'sql.detail.generatedSql': '생성된 SQL',
  'sql.detail.copy': '복사',
  'sql.detail.copied': '복사됨 ✓',
  'sql.detail.noSql': 'SQL이 생성되지 않았습니다.',
  'sql.detail.confidence': '신뢰도:',
  'sql.detail.validation': '검증:',
  'sql.detail.model': '모델:',
  'sql.detail.createdAt': '생성일시:',
  'sql.empty': '왼쪽에서 이력을 선택하거나 오른쪽 채팅에서 질문을 입력하세요.',
};

const translations: Record<Language, Translations> = { en, ko };

export const t = derived(language, ($lang) => (key: string, params?: Record<string, string | number>) => {
  let text = translations[$lang]?.[key] ?? translations.en[key] ?? key;
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      text = text.replaceAll(`{${k}}`, String(v));
    });
  }
  return text;
});
