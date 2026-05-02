# Frontend — AI Collaboration Guide

Svelte 4 + Vite 5 SPA. See [../CLAUDE.md](../CLAUDE.md) for the project-wide picture and [../prd/](../prd/) for feature specs. Target migration to SvelteKit is deferred — keep everything working on plain Svelte 4 until explicitly asked.

---

## Layout

App shell: top navigation bar + three-column body.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  App Bar                                                                    │
│  [SQL Helper]  [🗄️ Data Source]  [📚 Data Catalog]              [Profile]  │
├──────────────┬────────────────────────────────────┬────────────────────────┤
│  Nav Sidebar │   Conversation View (Main)         │  Session Panel         │
│  (200px)     │   (flex: 1)                        │  (260px)               │
│              │                                    │                        │
│  ▼ SQL       │  ╔══════════════════════╗          │  [+ New]               │
│   Assistant  │  ║ How many items were  ║ ← user   │                        │
│   ● my_db    │  ║ sold last month?     ║   bubble │  Recent                │
│   ● dev_db   │  ╚══════════════════════╝          │  ──────────────────    │
│  • Data      │                                    │  • Session A   Jan 12  │
│    Analysis  │  Item unit sold on April...        │    my_db               │
│  • Dashboard │  ``` sql                           │  • Session B   Jan 10  │
│              │  << Generated SQL >>               │    dev_db              │
│              │  ```                               │  (scrollable)          │
│              │  Data source:                      │                        │
│              │  1. ...  2. ...                    │                        │
│              │                                    │                        │
│              │  ┌──────────────────────────────┐  │                        │
│              │  │ User input                   │  │                        │
│              │  │ [Save conversation] [Analyze]│  │                        │
│              │  └──────────────────────────────┘  │                        │
└──────────────┴────────────────────────────────────┴────────────────────────┘
```

### Layout 구성 요소 (frontend 용어)

| 영역 | HTML/CSS 용어 | 설명 |
|------|--------------|------|
| 최상단 바 | `<header>` / App Bar | 앱 이름, 세션 탭, 프로필 |
| 세션 탭 | Tab Strip (Chrome-style tabs) | 여러 대화 세션을 탭으로 전환. `overflow-x: auto` 스크롤 가능 |
| 좌측 메뉴 | Nav Sidebar / Navigation Rail | 기능 페이지 전환. `position: sticky` |
| 중앙 대화 영역 | Conversation View | 메시지 버블 스크롤 + 하단 입력창 |
| 우측 세션 목록 | Session Panel / History Drawer | 대화 세션 목록. `overflow-y: auto` |

### 메시지 버블 (Conversation View 내부)

- **User message**: 오른쪽 정렬 말풍선 (`align-self: flex-end`, `border-radius` 말풍선형)
- **Assistant message**: 왼쪽 정렬 말풍선 (`align-self: flex-start`)
  - 자연어 텍스트 → SQL 코드블록 (`<pre><code>`) → Data source 번호 목록 순서로 렌더링
- 메시지 컨테이너: `display: flex; flex-direction: column; gap: 12px; overflow-y: auto`
- 새 메시지 도착 시 `scrollIntoView({ behavior: 'smooth' })` 자동 스크롤

### 입력 영역 (Prompt Input Bar)

하단 고정 (`position: sticky; bottom: 0`):
- 텍스트 입력 (`<textarea>` auto-resize)
- **Save conversation** 버튼 — 현재 세션 저장
- **Go to analysis** 버튼 (`primary CTA`) — 생성된 SQL을 Data Analysis 페이지로 전달

### 현재 ChatPanel과의 차이점

기존 CLAUDE.md의 우측 `ChatPanel`은 아래와 같이 역할이 분리된다:
- 대화 메시지 UI → **Conversation View** (중앙 메인 영역)
- 세션 관리 → **Session Panel** (우측 패널)
- 세션 탭 전환 → **Tab Strip** (상단 App Bar 내)

---

## Directory structure

```
frontend/src/
├── App.svelte                      — App shell: header + 3-column body + session state. onMount에서 data source 목록 로드
├── main.ts                         — mounts App
├── style.css                       — CSS variables + resets
├── lib/
│   ├── types.ts                    — TypeScript types (mirror backend Pydantic schemas)
│   ├── api.ts                      — Typed API client (Feature 1 real; others stubbed)
│   ├── stores.ts                   — Svelte stores (sessions, activeMenu, dataSources, selectedDataSource 등)
│   └── mock.ts                     — Mock data for Features 2-6
└── components/
    ├── layout/
    │   ├── AppBar.svelte           — 상단 48px 바: 로고(좌) + [Data Source][Data Catalog] 탭(중앙) + Profile(우)
    │   ├── TabStrip.svelte         — Chrome-style 세션 탭 (탭 추가/닫기/전환)
    │   ├── NavSidebar.svelte       — 좌측 메뉴: SQL Assistant 아코디언(커넥션 리스트) + Data Analysis + Dashboard
    │   └── SessionPanel.svelte     — 우측 대화 세션 목록 + 커넥션 이름 뱃지
    ├── conversation/
    │   ├── ConversationView.svelte — 중앙 메시지 버블 스크롤 영역
    │   ├── MessageBubble.svelte    — user / assistant 말풍선 (role prop으로 분기)
    │   ├── SqlBlock.svelte         — assistant 응답 내 SQL 코드블록 렌더링
    │   └── PromptInputBar.svelte   — 하단 입력창 + Save / Go to Analysis 버튼
    ├── shared/
    │   └── EmptyDataSource.svelte  — 데이터 소스 미등록/미선택 시 공통 안내 화면 (reason prop)
    ├── DataSource.svelte           — Feature 1: data source CRUD (real backend). CRUD 후 dataSources/selectedDataSource store 동기화
    ├── DataCatalog.svelte          — Feature 2+3: Browse 탭(스키마 트리+컬럼 상세) + Search 탭(벡터 유사도 검색). selectedDataSource 필요
    ├── TextToSQL.svelte            — Feature 4: SQL generation history (mock). selectedDataSource 필요
    ├── DataAnalysis.svelte         — Feature 5: query execution + stats (mock). selectedDataSource 필요
    └── Dashboard.svelte            — Feature 6: dashboard widgets (mock). selectedDataSource 필요
```

> **현재 `ChatPanel.svelte`**: `ConversationView` + `PromptInputBar` + `SessionPanel`로 분리 예정. 리팩토링 전까지는 `ChatPanel.svelte` 유지.

---

## 컴포넌트별 책임 (Component Responsibility Map)

> 검토 시 각 파일이 이 설명대로 동작하는지 확인하세요.

### Layout 컴포넌트

| 파일 | 책임 | 핵심 props / stores |
|------|------|---------------------|
| `App.svelte` | 전체 앱 셸. `<header> + .body(flex row)` 구조 유지. activeMenu에 따라 center 컴포넌트 교환. SQL Assistant일 때만 TabStrip+SessionPanel 렌더링. `onMount`에서 data source 로드 | `sessions`, `activeSessionId`, `activeMenu`, `dataSources`, `selectedDataSource` (stores) |
| `layout/AppBar.svelte` | 상단 48px 바. 로고(좌) + [Data Source][Data Catalog] 탭(중앙) + Profile(우). 탭 클릭 → `activeMenu.set(...)` | `sidebarCollapsed`, `activeMenu` (stores) |
| `layout/TabStrip.svelte` | Chrome-style 탭 스트립. 탭 클릭→세션 전환, × 클릭→세션 제거, + 클릭→새 세션. `overflow-x: auto` | `sessions`, `activeId` props; `activeSessionId`, `addSession`, `removeSession` (stores) |
| `layout/NavSidebar.svelte` | 300px 좌측 메뉴. SQL Assistant 아코디언(커넥션 클릭 → `openOrCreateSession`) + Data Analysis + Dashboard. activeMenu=sql-assistant 시 아코디언 자동 펼침 | `activeMenu`, `dataSources`, `sidebarCollapsed` (stores); `openOrCreateSession` |
| `layout/SessionPanel.svelte` | 240px 우측 대화 목록. 세션마다 제목 + 날짜/커넥션 이름 뱃지 표시 | `sessions` prop; `activeSessionId`, `dataSources` (stores) |
| `shared/EmptyDataSource.svelte` | 데이터 소스 미등록(`reason="none"`) 또는 미선택(`reason="select"`) 상태 안내 화면. `none`일 때 "데이터 소스 등록하기" CTA 버튼 표시 | `activeMenu` (store) |

### Conversation 컴포넌트

| 파일 | 책임 | 핵심 props / events |
|------|------|---------------------|
| `conversation/ConversationView.svelte` | 대화의 orchestrator. 메시지 목록 렌더링, mock SQL 생성 로직 보유, `afterUpdate`로 자동 스크롤 | `session: Session` prop; `addMessage`, `pendingSql`, `activeMenu` (stores) |
| `conversation/MessageBubble.svelte` | 단일 말풍선. `role=user` → 우측 파란 버블, `role=assistant` → 좌측 어두운 버블. sql 있으면 SqlBlock, dataSources 있으면 번호 목록 렌더링 | `message: Message` prop |
| `conversation/SqlBlock.svelte` | SQL 코드블록 UI. 상단 헤더(SQL 레이블 + Copy 버튼) + `<pre>` 코드 영역. 클립보드 복사 후 1.5초 "Copied ✓" 피드백 | `sql: string` prop |
| `conversation/PromptInputBar.svelte` | 하단 입력 영역. `<textarea>` auto-resize (Enter 전송 / Shift+Enter 줄바꿈). Save / Go to analysis 버튼. analysis 버튼은 `pendingSql !== null`일 때만 활성화 | `hasPendingSql: boolean` prop; `send`, `save`, `analyze` events |

### 상태 흐름 (State Flow)

```
stores.ts
  sessions[]            — 전체 세션 목록 (writable). Session에 dataSourceId 포함
  activeSessionId       — 현재 활성 세션 ID (writable)
  activeMenu            — 현재 선택된 메뉴 (writable)
  pendingSql            — "Go to analysis" 전달용 SQL (writable)
  dataSources[]         — 전체 데이터 소스 목록 (writable)
  selectedDataSource    — 현재 선택된 데이터 소스 (writable, null 가능)

  addSession(dataSourceId?)  — 새 세션 생성. 커넥션 인사 메시지 포함
  openOrCreateSession(source) — 해당 소스의 최신 세션을 열거나 없으면 신규 생성
                               → selectedDataSource.set(source)

App.svelte (onMount)
  dataSourceApi.list()
    → dataSources.set(list)
    → selectedDataSource.set(list[0] ?? null)

DataSource.svelte (load 후)
  dataSources.set(sources)
  selectedDataSource.update(cur =>
    sources.find(s => s.id === cur?.id) ?? sources[0] ?? null
  )

NavSidebar.svelte
  커넥션 클릭 → openOrCreateSession(source)   // selectedDataSource도 자동 업데이트

Feature 2-6 페이지 (Data Catalog, Analysis, Dashboard 등)
  $dataSources.length === 0  → EmptyDataSource reason="none"
  !$selectedDataSource       → EmptyDataSource reason="select"
  else                       → 정상 렌더링

App.svelte
  $: currentSession = sessions.find(s => s.id === $activeSessionId)
  → ConversationView에 session prop으로 전달

ConversationView.svelte
  handleSend() → addMessage(sessionId, userMsg)
             → await mock delay
             → addMessage(sessionId, assistantMsg)
             → pendingSql.set(sql)

PromptInputBar
  "Go to analysis" click → activeMenu.set('data-analysis')
```

---

## Backend integration status

| Feature | Component | Backend | Notes |
|---|---|---|---|
| 1. Data Source | `DataSource.svelte` | **Real** | CRUD + test + sync via `/api/v1/data-sources` |
| 2+3. Data Catalog | `DataCatalog.svelte` | **Real** | Browse: `GET /api/v1/data-catalog/sources/{id}` + lazy `GET .../tables/{id}`. Search: `POST /api/v1/data-catalog/semantic-search`. Refresh: `POST /api/v1/data-catalog/refresh` |
| 4. Text-to-SQL | `TextToSQL.svelte` | Mock | Chat panel holds the real UX; history is mock |
| 5. Data Analysis | `DataAnalysis.svelte` | Mock | Awaiting Feature 5 backend |
| 6. Dashboard | `Dashboard.svelte` | Mock | Awaiting Feature 6 backend |
| Chat Panel | `ChatPanel.svelte` | Mock | Will wire to `POST /api/v1/text-to-sql/generate` (streaming SSE) |

---

## API client (`src/lib/api.ts`)

Single module — one exported object per backend controller:

```ts
export const dataSourceApi = {
  list, get, create, update, delete, testConnection, sync, testConnectionDirect
};
export const dataCatalogApi = {
  getSourceCatalog, getTableDetail, semanticSearch, refresh
};
// Future: textToSqlApi, dataAnalysisApi, dashboardApi
```

Base URL resolved from `VITE_BACKEND_URL` env var → falls back to `window.location.origin` with `:3000` → `:8000` replacement.

Errors throw `ApiError(status, message)` — never `alert()`. Components catch and render inline error states.

---

## Conversation (SQL Assistant)

### Session 모델

```ts
interface Session {
  id: string;
  title: string;           // 첫 user 메시지 앞 20자 자동 생성
  createdAt: Date;
  messages: Message[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sql?: string;            // assistant 응답에 SQL이 포함된 경우
  dataSources?: string[];  // 응답에 포함된 data source 참조 목록
  createdAt: Date;
}
```

- 세션은 **App.svelte** 에서 `Session[]`로 관리 (svelte store 사용)
- 탭 하나 = 세션 하나. 탭 전환 시 해당 세션의 `Message[]` 렌더링
- **Session Panel** 은 전체 세션 목록, **Tab Strip** 은 현재 열린 세션만 표시

### ConversationView 동작

- `messages` prop 배열을 순서대로 `MessageBubble` 렌더링
- `role === 'user'`: 오른쪽 정렬 버블
- `role === 'assistant'`: 왼쪽 정렬 버블. `sql` 필드 있으면 `SqlBlock` 삽입, `dataSources` 있으면 번호 목록 추가
- 메시지 추가 시 `scrollIntoView({ behavior: 'smooth' })` 자동 스크롤

### PromptInputBar 동작

- `<textarea>` — `rows` 1 기본, 입력에 따라 auto-resize (`scrollHeight` 기반)
- `Shift+Enter`: 줄바꿈, `Enter`: 전송
- **Save conversation** 버튼: 현재 세션을 백엔드(또는 로컬스토리지)에 저장
- **Go to analysis** 버튼 (`primary`): 마지막으로 생성된 SQL을 Data Analysis 컴포넌트로 전달 (`svelte/store` 경유)

### 백엔드 연동 (Feature 4 준비되면)

현재 mock → `POST /api/v1/text-to-sql/generate` (streaming SSE) 교체:
```ts
const res = await fetch('/api/v1/text-to-sql/generate', { method: 'POST', body });
const reader = res.body.getReader();
// chunk 수신마다 assistant 메시지에 append
```

---

## Feature 1 — Data Source (real)

`DataSource.svelte` wires to all 7 endpoints:
- `GET /api/v1/data-sources` — list
- `POST /api/v1/data-sources` — create (type-specific config form)
- `PUT /api/v1/data-sources/{id}` — inline description edit
- `DELETE /api/v1/data-sources/{id}` — delete with confirm
- `POST /api/v1/data-sources/{id}/test` — connection test → badge update
- `POST /api/v1/data-sources/{id}/sync` — catalog sync (returns 202)

Config form adapts to type:
- **postgresql / redshift**: host, port, database, username, password
- **trino**: coordinator_url, catalog, username, password

Password is never shown after save (backend strips it from responses).

---

## Features 2-6 — Mock

Mock data lives in `src/lib/mock.ts`. When a Feature N backend is ready:
1. Remove the mock import from the component
2. Add the real API call to `api.ts`
3. Replace the component's data binding

---

## Conventions

- `<script lang="ts">` on every component
- Scoped `<style>` per component; shared variables via `style.css` CSS custom properties
- No Tailwind, no UI component libraries
- No `alert()` — inline error states only
- State: local to each component; `svelte/store` only when two components truly share state (currently: none)
- No additional npm packages unless explicitly needed

---

## Running locally

```bash
cd frontend && npm install && npm run dev
# → http://localhost:3000
# requires backend on :8000
```

Or: `./bin/run-frontend.sh`
