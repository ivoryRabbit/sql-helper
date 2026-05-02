# SQL Helper — Workflow & 진행 상황

> 마지막 업데이트: 2026-05-02 (Feature 4 Data Analysis 백엔드 완료 — execute/stats/insights/export 구현, adapters에 execute_query 추가)
> 구현 순서: Feature 1 → 2 → 3 → 4 → 5

---

## User Journey

```
 1. Sources   →   2. Catalog (Browse + Search)   →   3. Text-to-SQL   →   4. Analysis   →   5. Dashboards
 (connect DB)     (generate + browse + semantic)      (gen SQL, SSE)        (run + read)      (save HTML)
```

탭 간 하드 게이트는 없으나, 선행 조건이 없으면 인라인 안내("Register a data source first")를 표시한다.

---

## 백엔드 플로우 요약

| Feature | 핵심 플로우 |
|---|---|
| **1. Data Source** | POST → adapter.test_connection() → DB insert. config는 JSONB, 민감 필드 암호화. |
| **2. Data Catalog** | `POST /refresh` → Temporal `CatalogGenerationWorkflow` (introspect + embed 배치) → pgvector upsert. Browse/Search는 동기 조회. Semantic search는 embedding → pgvector cosine distance. |
| **3. Text-to-SQL** | `POST /generate` → embed query → semantic_search(docs) → build_messages → LLM stream → extract_sql → validate_syntax → save. SSE로 스트리밍. Session 기반 multi-turn 지원. |
| **4. Data Analysis** | `POST /analyze` → adapter.execute(sql) → row_batch SSE → `AnalysisAgent` (describe_stats → summarize) → `analysis_session` 저장. |
| **5. Dashboard** | Frontend가 HTML 렌더링 → `POST /dashboards` → MinIO put → DB insert. 조회 시 presigned URL 반환. |

**Temporal을 쓰는 이유**: 카탈로그 인트로스펙션 + 임베딩 생성은 수 분이 걸려 API 블로킹 불가; 재시작 시 상태 유실 방지.

**에러 처리**:
- Adapter 오류 → HTTP 502, LLM 오류 → HTTP 503 + `error` SSE, SQL 검증 실패는 에러가 아닌 `repair_sql` 반복.
- 선행 조건 미충족 → HTTP 409 + `code` (e.g. `"catalog_empty"`).

---

## 전체 현황

| 항목 | 상태 |
|------|------|
| **인프라** | 🟢 완료 (PostgreSQL + Temporal + MinIO, docker-compose 완성) |
| **Feature 1: Data Source** | 🟢 Backend 완료 (Frontend 미연동) |
| **Feature 2: Data Catalog** | 🟢 Backend 완료 (Browse + Semantic Search 통합, Frontend 미연동) |
| **Feature 3: Text-to-SQL** | 🟢 Backend 완료 (Frontend 미연동) |
| **Feature 4: Data Analysis** | 🟢 Backend 완료 (Frontend 미연동) |
| **Feature 5: Dashboard** | ⬜ 미구현 |

> **Feature 2 통합 안내**: Data Catalog와 Data Discovery(Semantic Search)는 단일 Feature 2로 통합됨.
> PRD 파일 기준: `prd/2_data_catalog.md`, 백엔드: `DataCatalogService`, 엔드포인트: `/api/v1/data-catalog/**`.

---

## 0. 인프라 (prd/0_infra.md)

### Docker Compose 서비스

- [x] PostgreSQL (pgvector:pg17) — 포트 5432
- [x] Temporal (temporalio/auto-setup) — 포트 7233
- [x] Temporal UI — 포트 8088
- [x] MinIO — 포트 9000/9001
- [ ] Backend (FastAPI) — 포트 8000 (로컬 `run-backend.sh` 사용 중)
- [ ] Frontend (SvelteKit) — 포트 3000 (로컬 `run-frontend.sh` 사용 중)

### DB 초기화

- [x] `docker/vectordb/init_db.sql` — `data_catalog` 스키마 생성
- [x] 전체 테이블 DDL — `ModelBase.metadata.create_all`로 앱 시작 시 자동 생성

### Backend 프로젝트 구조

- [x] `backend/Dockerfile`
- [x] `backend/requirements.txt` — minio, temporalio 추가
- [x] `backend/src/main.py` — FastAPI 진입점 (Temporal 연결 + MinIO 버킷 초기화 포함)
- [x] `backend/src/configs/settings.py`
- [x] `backend/src/configs/container.py` — DI 컨테이너 (StorageClient, TemporalClient 등록)
- [x] `backend/src/configs/routers.py`
- [x] `backend/src/components/database_manager.py`
- [x] `backend/src/dependencies.py`
- [x] `backend/src/clients/storage.py` — MinIO 클라이언트
- [x] `backend/src/clients/temporal.py` — Temporal 클라이언트
- [x] `.env.example` — 전체 환경변수 문서화

### Frontend 프로젝트 구조

- [x] Svelte 4 + Vite 5 기본 세팅
- [x] `frontend/src/lib/api.ts` — API 클라이언트
- [x] `frontend/src/lib/types.ts` — TypeScript 타입
- [x] `frontend/src/lib/mock.ts` — 목 데이터
- [ ] SvelteKit 마이그레이션

---

## Feature 1: Data Source (prd/1_data_source.md)

### DB 테이블

- [x] `data_catalog.data_sources` 테이블 — `entities.py` DataSource 엔티티로 자동 생성

### Backend

- [x] `backend/src/models/entities.py` — `DataSource` 엔티티
- [x] `backend/src/models/request/data_source.py`
- [x] `backend/src/models/response/data_source.py`
- [x] `backend/src/repositories/base.py`
- [x] `backend/src/repositories/data_source.py`
- [x] `backend/src/services/data_source.py`
- [x] `backend/src/controllers/data_source.py`
- [x] `backend/src/utils/crypto.py` — Fernet 암호화 (AES-128-CBC)
- [x] `backend/src/adapters/postgres.py` — PostgreSQL 커넥터
- [x] `backend/src/adapters/redshift.py` — Redshift 커넥터
- [x] `backend/src/adapters/trino.py` — Trino 커넥터
- [x] `POST /api/v1/data-sources` — 생성
- [x] `GET /api/v1/data-sources` — 목록
- [x] `GET /api/v1/data-sources/{id}` — 상세
- [x] `PUT /api/v1/data-sources/{id}` — 수정
- [x] `DELETE /api/v1/data-sources/{id}` — 삭제
- [x] `POST /api/v1/data-sources/{id}/test` — 연결 테스트
- [x] `POST /api/v1/data-sources/{id}/sync` — 스키마 동기화 (DataCatalogService.refresh 연동)
- [x] `GET /api/v1/data-sources/{id}/health` — 헬스 체크

### Frontend

- [x] `frontend/src/components/DataSource.svelte` — UI 셸 (목 데이터)
- [ ] 실제 API 연동

---

## Feature 2: Data Catalog (prd/2_data_catalog.md)

> Browse + Semantic Search 통합. 단일 `DataCatalogService`가 두 기능을 모두 처리.

### DB 테이블

- [x] `data_catalog.schemas` 테이블
- [x] `data_catalog.tables` 테이블
- [x] `data_catalog.columns` 테이블
- [x] `data_catalog.table_documents` 테이블 (VECTOR(384), HNSW 인덱스)
- [x] `data_catalog.search_history` 테이블

### Backend

- [x] `backend/src/models/entities.py` — `Schema`, `Table`, `Column`, `TableDocument`, `SearchHistory` 엔티티
- [x] `backend/src/models/request/data_catalog.py`
- [x] `backend/src/models/response/data_catalog.py`
- [x] `backend/src/repositories/data_catalog.py`
- [x] `backend/src/repositories/table_document.py` — pgvector cosine 검색
- [x] `backend/src/repositories/search_history.py`
- [x] `backend/src/services/data_catalog.py` — Browse + Semantic Search 통합
- [x] `backend/src/controllers/data_catalog.py`
- [x] `backend/src/clients/embedding.py` — `all-MiniLM-L6-v2` 임베딩
- [x] `GET /api/v1/data-catalog/sources/{id}` — 소스별 카탈로그
- [x] `GET /api/v1/data-catalog/tables` — 테이블 목록
- [x] `GET /api/v1/data-catalog/tables/{id}` — 테이블 상세
- [x] `GET /api/v1/data-catalog/schemas` — 스키마 목록
- [x] `GET /api/v1/data-catalog/search` — 테이블/컬럼 이름 검색
- [x] `POST /api/v1/data-catalog/refresh` — 카탈로그 갱신
- [x] `GET /api/v1/data-catalog/stats` — 통계
- [x] `POST /api/v1/data-catalog/semantic-search` — 시맨틱 검색
- [x] `POST /api/v1/data-catalog/similar` — 유사 테이블 탐색
- [x] `GET /api/v1/data-catalog/recommendations` — 추천
- [x] `GET /api/v1/data-catalog/history` — 검색 이력
- [ ] Temporal 워크플로우 — 카탈로그 동기화 비동기화 (현재 동기 실행)

### Frontend

- [x] `frontend/src/components/DataCatalog.svelte` — UI 셸 (목 데이터)
- [ ] 실제 API 연동

---

## Feature 3: SQL Assistant (prd/3_sql_assistant.md)

### DB 테이블

- [x] `data_catalog.conversation_sessions` 테이블
- [x] `data_catalog.sql_generations` 테이블
- [x] `data_catalog.conversation_messages` 테이블

### Backend

- [x] `backend/src/models/entities.py` — `ConversationSession`, `SqlGeneration`, `ConversationMessage` 엔티티
- [x] `backend/src/models/request/sql_assistant.py`
- [x] `backend/src/models/response/sql_assistant.py`
- [x] `backend/src/repositories/sql_assistant.py` — `SqlGenerationRepository`, `ConversationSessionRepository`, `ConversationMessageRepository`
- [x] `backend/src/clients/llm.py` — AsyncOpenAI 클라이언트 (stream_generate 포함)
- [x] `backend/src/services/sql_assistant.py` — RAG 파이프라인 (embed → semantic_search → build_messages → LLM stream → extract_sql → validate)
- [x] `backend/src/controllers/sql_assistant.py`
- [x] `backend/src/agents/docs/postgresql.md` — PostgreSQL 시스템 프롬프트
- [x] `backend/src/agents/docs/mysql.md` — MySQL 시스템 프롬프트
- [x] `backend/src/agents/docs/sqlite.md` — SQLite 시스템 프롬프트
- [x] `POST /api/v1/sql-assistant/generate` — SQL 생성 (SSE 스트리밍)
- [x] `POST /api/v1/sql-assistant/validate` — SQL 검증 (syntax + security)
- [x] `POST /api/v1/sql-assistant/explain` — SQL 설명
- [x] `POST /api/v1/sql-assistant/optimize` — SQL 최적화
- [x] `GET /api/v1/sql-assistant/history` — 생성 이력
- [x] `POST /api/v1/sql-assistant/sessions` — 세션 생성
- [x] `GET /api/v1/sql-assistant/sessions` — 세션 목록
- [x] `GET /api/v1/sql-assistant/sessions/{id}` — 세션 상세
- [x] `DELETE /api/v1/sql-assistant/sessions/{id}` — 세션 삭제

### Frontend

- [x] `frontend/src/components/TextToSQL.svelte` — UI 셸 (목 데이터)
- [ ] SSE 스트리밍 수신 구현
- [ ] 실제 API 연동

---

## Feature 4: Data Analysis (prd/4_data_analysis.md)

### DB 테이블

- [x] `data_catalog.analysis_executions` 테이블 — `entities.py`로 자동 생성
- [x] `data_catalog.analysis_results` 테이블 — `entities.py`로 자동 생성
- [x] `data_catalog.analysis_insights` 테이블 — `entities.py`로 자동 생성

### Backend

- [x] `backend/src/models/entities.py` — `AnalysisExecution`, `AnalysisResult`, `AnalysisInsight` 엔티티 추가
- [x] `backend/src/models/request/data_analysis.py`
- [x] `backend/src/models/response/data_analysis.py`
- [x] `backend/src/repositories/data_analysis.py`
- [x] `backend/src/services/data_analysis.py` — 통계 계산, 인사이트 생성, 시각화 추천, export
- [x] `backend/src/controllers/data_analysis.py`
- [x] `backend/src/adapters/base.py` — `execute_query()` 추상 메서드 추가
- [x] `backend/src/adapters/postgres.py` — `execute_query()` 구현 (psycopg v3)
- [x] `backend/src/adapters/redshift.py` — `execute_query()` 구현 (psycopg v3)
- [x] `backend/src/adapters/trino.py` — `execute_query()` 구현 (Trino REST API)
- [x] `POST /api/v1/data-analysis/execute` — SQL 실행 + 통계 + 인사이트 + 시각화 추천
- [x] `GET /api/v1/data-analysis/results/{id}` — 결과 조회
- [x] `GET /api/v1/data-analysis/history` — 실행 이력
- [x] `POST /api/v1/data-analysis/export` — CSV/JSON 내보내기 (MinIO presigned URL 반환)
- [ ] Temporal 워크플로우 — 비동기 쿼리 실행 (현재 동기 실행)

### Frontend

- [x] `frontend/src/components/DataAnalysis.svelte` — UI 셸 (목 데이터)
- [ ] 실제 API 연동

---

## Feature 5: Dashboard (prd/5_dashboard.md)

### DB 테이블

- [ ] `data_catalog.dashboards` 테이블 생성
- [ ] `data_catalog.dashboard_widgets` 테이블 생성

### Backend

- [ ] `backend/src/models/entities.py` — `Dashboard`, `DashboardWidget` 엔티티 추가
- [ ] `backend/src/models/request/dashboard.py`
- [ ] `backend/src/models/response/dashboard.py`
- [ ] `backend/src/repositories/dashboard.py`
- [ ] `backend/src/services/dashboard.py`
- [ ] `backend/src/controllers/dashboard.py`
- [ ] `POST /api/v1/dashboards` — 생성
- [ ] `GET /api/v1/dashboards` — 목록
- [ ] `GET /api/v1/dashboards/{id}` — 조회
- [ ] `PUT /api/v1/dashboards/{id}` — 수정
- [ ] `DELETE /api/v1/dashboards/{id}` — 삭제
- [ ] `POST /api/v1/dashboards/{id}/widgets` — 위젯 추가
- [ ] `PUT /api/v1/dashboards/{id}/widgets/{wid}` — 위젯 수정
- [ ] `DELETE /api/v1/dashboards/{id}/widgets/{wid}` — 위젯 삭제
- [ ] `GET /api/v1/dashboards/{id}/html` — HTML 렌더링
- [ ] `POST /api/v1/dashboards/{id}/share` — 공유 링크 생성
- [ ] MinIO 연동 — HTML/PDF/이미지 내보내기

### Frontend

- [x] `frontend/src/components/Dashboard.svelte` — UI 셸 (목 데이터)
- [ ] GridStack 레이아웃 구현
- [ ] 실제 API 연동

---

## 진행 상황 요약

```
인프라       [██████████]  100% — PostgreSQL + Temporal + MinIO + docker-compose 완료
Feature 1   [████████░░]   80% — Backend 완료, Frontend 미연동
Feature 2   [████████░░]   80% — Backend 완료 (Browse + Search 통합), Frontend 미연동
Feature 3   [████████░░]   80% — Backend 완료 (SSE 스트리밍, 세션 관리), Frontend 미연동
Feature 4   [████████░░]   80% — Backend 완료 (실행, 통계, 인사이트, export), Frontend 미연동
Feature 5   [░░░░░░░░░░]    0% — 미구현
```

### 다음 우선 작업

1. **Feature 5 착수** — `dashboard` 백엔드 구현 (CRUD, MinIO HTML 저장, 위젯 관리)
2. **Frontend 연동** — Feature 1~4 API 실제 연결 (DataSource, DataCatalog, TextToSQL, DataAnalysis)
3. **Temporal 워크플로우** — 카탈로그 동기화 비동기화 (`catalog_sync.py` 구현)
