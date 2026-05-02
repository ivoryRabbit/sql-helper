# Architecture

System-level design for the text-to-SQL service. Read [WORKFLOW.md](WORKFLOW.md) for the per-feature flows and user journey; read [CLAUDE.md](CLAUDE.md) for project overview and conventions.

---

## Pipeline

The product is a linear pipeline the user walks through — each step consumes the previous step's output.

```
┌──────────────┐   ┌───────────────────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Data Source  │──▶│       Data Catalog        │──▶│ Text-to-SQL  │──▶│Data Analysis │──▶│  Dashboard   │
│  (register)  │   │ (generate + search/browse)│   │   (agent)    │   │   (agent)    │   │ (HTML in S3) │
└──────────────┘   └───────────────────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

Each feature is one backend service, one frontend tab, one set of controllers/repositories.

---

## Component topology

```
┌─────────────────┐             ┌──────────────────────────────────────┐
│  SvelteKit UI   │  HTTP + SSE │  FastAPI (backend/src/main.py)       │
│  (5 tabs)       │─────────────▶                                      │
└─────────────────┘             │  controllers → services → {          │
                                │    repositories  → app Postgres      │
                                │    adapters      → user databases    │
                                │    agents+skills → LLM provider      │
                                │    clients       → MinIO, Temporal   │
                                │  }                                   │
                                └────────────────────┬─────────────────┘
                                                     │ start_workflow
                                                     ▼
┌────────────────────┐             ┌──────────────────────────────────┐
│ Temporal cluster   │◀────────────│  Temporal worker process         │
│ (docker)           │   task poll │  (backend/src/worker.py)         │
└────────────────────┘             │   workflows/, activities/        │
                                   └──────────────────────────────────┘

┌──────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────┐
│ Postgres + pgvector  │  │ MinIO (S3 API)      │  │ LLM provider (OpenAI)   │
│ schema: data_catalog │  │ bucket: dashboards  │  │ (pluggable)             │
└──────────────────────┘  └─────────────────────┘  └─────────────────────────┘
```

Three processes long-running in dev: **API server**, **Temporal worker**, and the **Temporal cluster itself** (plus Postgres and MinIO containers). The API server does not execute long jobs directly — it submits workflows and returns a workflow ID.

---

## Layers (backend)

```
backend/src/
├── main.py                    # FastAPI app, lifespan, DI wiring
├── worker.py                  # Temporal worker entrypoint (NEW)
├── components/
│   └── database_manager.py    # AsyncEngine for app Postgres (existing)
├── configs/
│   ├── settings.py            # env-driven settings (DB, MinIO, Temporal, LLM)
│   ├── container.py           # dependency-injector AppContainer
│   └── routers.py             # FastAPI router registry
├── controllers/               # HTTP layer (one per feature)
│   ├── data_source.py
│   ├── data_catalog.py        # browse + semantic search endpoints
│   ├── sql_assistant.py       # NEW
│   ├── data_analysis.py       # NEW
│   └── dashboard.py           # NEW
├── services/                  # Orchestration (one per feature)
│   ├── data_source.py
│   ├── data_catalog.py        # catalog refresh (Temporal) + semantic search
│   ├── sql_assistant.py       # wraps SQLAgent
│   ├── data_analysis.py       # wraps AnalysisAgent
│   └── dashboard.py           # upload HTML + persist metadata
├── repositories/              # DB access (one per entity)
│   ├── base.py                # existing BaseRepository
│   ├── data_source.py
│   ├── table_document.py      # NEW — pgvector queries
│   ├── search_history.py
│   ├── analysis_session.py    # NEW
│   └── dashboard.py           # NEW
├── adapters/                  # NEW — user data-source connectors
│   ├── base.py                # DataSourceAdapter ABC
│   ├── postgres.py
│   ├── trino.py
│   └── registry.py            # type → adapter class
├── agents/                    # NEW — LLM orchestrators
│   ├── base.py                # Agent base + tool-calling loop
│   ├── sql_agent.py
│   └── analysis_agent.py
├── skills/                    # NEW — tools agents can call
│   ├── base.py                # Skill protocol
│   ├── catalog.py             # retrieve_tables, get_ddl
│   ├── sql.py                 # validate_sql, repair_sql
│   ├── execution.py           # run_sql (via adapter)
│   └── analysis.py            # describe_stats, summarize
├── prompts/                   # NEW — system prompts (markdown)
│   ├── sql_agent.md
│   └── analysis_agent.md
├── workflows/                 # NEW — Temporal workflow defs
│   └── catalog.py             # CatalogGenerationWorkflow
├── activities/                # NEW — Temporal activities
│   └── catalog.py             # introspect, embed, upsert
├── clients/                   # NEW — external infra clients
│   ├── llm.py                 # LLM provider (OpenAI first)
│   ├── object_storage.py      # MinIO/S3 client
│   └── temporal.py            # Temporal client wrapper
└── models/
    ├── entities.py            # ORM entities (+ Dashboard, AnalysisSession)
    ├── request/
    └── response/
```

### Rules between layers

- **Controllers** validate input, call **services**, serialize responses. No SQL, no LLM calls.
- **Services** orchestrate — they may call multiple repositories, adapters, agents, clients. They hold the business logic.
- **Repositories** access the app Postgres (`data_catalog` schema) via `AsyncSession`. Never access user databases.
- **Adapters** access user-registered databases (Postgres, Trino, ...) for introspection and query execution. Never touch app Postgres.
- **Agents** and **skills** are called only from services (text-to-SQL, analysis). They do not know about HTTP.
- **Workflows/activities** run in the Temporal worker process. Activities may call adapters, repositories (via a separate session factory), and clients.

---

## Data model

All tables live in the `data_catalog` schema (the app's metadata DB — not to be confused with user data sources).

### Existing

| Table | Purpose |
|---|---|
| `data_source` | Registered database connections (id, name, type, description, config JSON, timestamps). |
| `search_history` | User-asked questions (id, query, result_summary, created_at). |
| `table_documents` | pgvector-indexed catalog entries: `(id, document_type, schema_name, table_name, title, content, tags TEXT[], embedding VECTOR(384), timestamps)`. `document_type ∈ {ddl, doc, example}`. HNSW index with `vector_cosine_ops`. |

### New

| Table | Purpose |
|---|---|
| `analysis_session` | One record per text-to-SQL + analysis run. Fields: `id, data_source_id (FK), question, generated_sql, result_preview JSON, stats_summary TEXT, created_at`. Referenced by dashboards. |
| `dashboard` | Metadata for user-saved dashboards. Fields: `id, name, description, object_key, analysis_session_id (FK, nullable), created_at, updated_at`. The HTML lives in MinIO at `object_key`; the record does not store HTML. |

Add both to [backend/src/models/entities.py](backend/src/models/entities.py). No new pgvector tables — catalog reuses `table_documents`.

---

## Agent and Skill design

**No agent framework.** LangChain / LlamaIndex / Claude Agent SDK all hide the prompt and the loop; we want both visible. Build a minimal tool-calling loop on top of the LLM provider's native tool-use API (OpenAI function calling, Anthropic tool_use).

### Skill contract

```python
# backend/src/skills/base.py
from typing import Protocol, Any

class Skill(Protocol):
    name: str
    description: str
    input_schema: dict          # JSON schema, fed to LLM as tool spec
    async def run(self, **kwargs) -> Any: ...
```

Skills are small, single-purpose, stateless. Dependencies (repos, adapters) are injected at construction.

### Agent contract

```python
# backend/src/agents/base.py
class Agent:
    system_prompt: str          # loaded from prompts/<name>.md at startup
    skills: list[Skill]
    llm: LLMClient
    max_iterations: int = 8

    async def run(self, user_message, context) -> AsyncIterator[AgentEvent]:
        """
        Loop:
          1. Call LLM with system_prompt + history + tool specs
          2. If LLM emits tool_use → execute matching skill → append tool_result → loop
          3. If LLM emits final text → yield final event → stop
        Yields events: token | tool_call | tool_result | final | error
        """
```

Events are streamed to the HTTP layer via `StreamingResponse` (SSE). The frontend renders token-by-token for text-to-SQL and analysis.

### System prompts

Live in `backend/src/prompts/*.md` — **plain markdown, editable without touching code**. Loaded at agent construction. Update these when the agent misbehaves; reserve code changes for skill or loop changes.

### Agents in scope

| Agent | Skills | Produces |
|---|---|---|
| `SQLAgent` | `retrieve_tables`, `get_ddl`, `get_examples`, `validate_sql`, `repair_sql` | SQL + reasoning trace |
| `AnalysisAgent` | `run_sql`, `describe_stats`, `summarize` | Result table + narrative + (optional) chart spec |

---

## External DB adapter layer

User-registered databases are reached only through `adapters/`. Interface:

```python
class DataSourceAdapter(Protocol):
    async def test_connection(self) -> None: ...
    async def list_schemas(self) -> list[str]: ...
    async def introspect_tables(self, schema: str) -> list[TableInfo]: ...
    async def fetch_sample_rows(self, table: str, limit: int = 5) -> list[dict]: ...
    async def explain(self, sql: str) -> str: ...
    async def execute(self, sql: str, limit: int = 1000) -> QueryResult: ...
```

- `postgres.py` — psycopg (reuse version 3) + async.
- `trino.py` — `trino` client (add to requirements when wiring).
- `registry.py` maps `DataSource.type` → adapter class + credential schema.

Adapters never share connection pools with the app Postgres. Per-source credentials are held in `DataSource.config` (JSON); encrypt in a follow-up before prod.

---

## Object storage (MinIO)

Dashboards are stored as **prerendered HTML in MinIO**. The frontend renders the HTML (it already has the components and data), POSTs it to `POST /api/v1/dashboards`, and the backend uploads it to MinIO and persists metadata.

- Client: `backend/src/clients/object_storage.py` — thin wrapper over `boto3` or `minio`. S3-compatible calls only, so MinIO locally / S3 in prod.
- Bucket: `dashboards` (create on startup if missing).
- Object key: `{dashboard_id}/{slug}.html`.
- Serve: `GET /api/v1/dashboards/{id}` returns metadata + a **presigned URL** (short TTL). The browser navigates to that URL directly — backend never proxies the HTML.

Add MinIO service to `docker-compose.yaml`:

```yaml
minio:
  image: minio/minio:latest
  ports: ["9000:9000", "9001:9001"]
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  command: server /data --console-address ":9001"
  volumes:
    - ./docker/volumes/minio:/data
```

---

## Temporal (catalog generation)

Catalog generation is long-running (introspect → embed N tables → upsert). Runs as a Temporal workflow so it survives API restarts and is resumable.

### Workflow

```python
# backend/src/workflows/catalog.py
@workflow.defn
class CatalogGenerationWorkflow:
    @workflow.run
    async def run(self, params: CatalogParams) -> CatalogResult:
        tables = await workflow.execute_activity(introspect_tables, params, ...)
        for batch in chunks(tables, 16):
            embeddings = await workflow.execute_activity(embed_batch, batch, ...)
            await workflow.execute_activity(upsert_documents, (batch, embeddings), ...)
        return CatalogResult(count=len(tables))
```

### Activities (live in `activities/catalog.py`)

- `introspect_tables(data_source_id)` — uses adapter to enumerate tables + columns.
- `embed_batch(texts)` — sentence-transformers on CPU.
- `upsert_documents(items)` — writes to `table_documents` with `document_type='ddl'`.

### Wiring

- `clients/temporal.py` exposes a `TemporalClient` singleton provided by `AppContainer`.
- `services/data_catalog.py` calls `client.start_workflow(CatalogGenerationWorkflow, ...)` and stores the workflow ID on the `data_source` record (or in a dedicated `catalog_run` table if we need history — defer until needed).
- `worker.py` is a separate entrypoint: `python -m worker`. Add a matching `bin/run-worker.sh`.
- Add Temporal + its Postgres to `docker-compose.yaml` (reuse the official `temporalio/auto-setup` image and a dedicated Postgres).

---

## Streaming contract

Two endpoints stream:

- `POST /api/v1/sql-assistant` — SSE events from `SQLAgent`. Event types: `tool_call`, `tool_result`, `token`, `final_sql`, `error`.
- `POST /api/v1/analysis` — SSE events from `AnalysisAgent`. Event types: `row_batch` (first N rows for preview), `stats`, `token`, `final_summary`, `error`.

Both return `text/event-stream`. The frontend consumes via `fetch` + `ReadableStream.getReader()` (no SSE library — see [frontend/CLAUDE.md](frontend/CLAUDE.md)).

---

## Configuration (env)

Extend `backend/src/configs/settings.py` with:

| Group | Keys |
|---|---|
| `DatabaseSettings` | `host, port, username, password, database, pool_size, max_overflow, pool_recycle` (existing) |
| `ObjectStorageSettings` | `endpoint, access_key, secret_key, bucket, secure` |
| `TemporalSettings` | `host, namespace, task_queue` |
| `LLMSettings` | `provider, model, api_key, base_url (optional)` |

Each group is a separate `BaseSettings` class, composed into an `AppSettings` container. Providers in `AppContainer` resolve per-group settings.

---

## API surface (target)

| Method | Path | Purpose |
|---|---|---|
| GET/POST/PUT/DELETE | `/api/v1/data-sources` | CRUD for registered DBs |
| POST | `/api/v1/data-sources/{id}/test` | Connection test via adapter |
| POST | `/api/v1/data-sources/{id}/sync` | Trigger `CatalogSyncWorkflow`; returns workflow_id |
| POST | `/api/v1/data-catalog/refresh` | Start `CatalogGenerationWorkflow`; returns workflow_id |
| GET | `/api/v1/data-catalog/sources/{id}` | Full catalog tree by data source |
| GET | `/api/v1/data-catalog/tables` | Browse table list |
| GET | `/api/v1/data-catalog/tables/{id}` | Table detail with columns |
| GET | `/api/v1/data-catalog/schemas` | Schema list |
| GET | `/api/v1/data-catalog/search` | Keyword search (table/column names) |
| GET | `/api/v1/data-catalog/stats` | Catalog statistics |
| POST | `/api/v1/data-catalog/semantic-search` | Vector similarity search (non-streaming) |
| POST | `/api/v1/data-catalog/similar` | Find similar tables |
| GET | `/api/v1/data-catalog/recommendations` | Table recommendations for a query |
| GET | `/api/v1/data-catalog/history` | Search history |
| POST | `/api/v1/sql-assistant/generate` | **Streaming** SQL generation (SSE) |
| POST | `/api/v1/sql-assistant/validate` | SQL syntax/semantic/injection validation |
| POST | `/api/v1/sql-assistant/explain` | SQL explanation |
| POST | `/api/v1/sql-assistant/optimize` | SQL optimization suggestions |
| GET | `/api/v1/sql-assistant/history` | Generation history |
| POST | `/api/v1/data-analysis/execute` | Execute SQL + **streaming** row batches |
| POST | `/api/v1/data-analysis/analyze` | **Streaming** AnalysisAgent summarization |
| GET | `/api/v1/data-analysis/results/{id}` | Stored analysis result |
| GET | `/api/v1/data-analysis/history` | Execution history |
| POST | `/api/v1/data-analysis/export` | Export to CSV/JSON/Excel (MinIO) |
| GET/POST/PUT/DELETE | `/api/v1/dashboards` | Upload/list/update/delete saved dashboards |
| GET | `/api/v1/dashboards/{id}` | Metadata + presigned MinIO URL |
| POST | `/api/v1/dashboards/{id}/share` | Create public share link |
| GET | `/health` | Basic service liveness |
| GET | `/health/db` | Postgres connectivity |
| GET | `/health/temporal` | Temporal connectivity |
| GET | `/health/minio` | MinIO connectivity |

---

## Non-goals (explicit)

- **No multi-tenant auth.** Single-user assumption for now; revisit before prod.
- **No scheduled catalog refresh.** Manual rebuild only; cron is a later Temporal schedule.
- **No query cost estimation.** Defer until EXPLAIN-based pricing becomes necessary.
- **No agent memory across sessions.** Each text-to-SQL call is stateless; conversation context is passed client-side.
- **No dashboard edit-in-place.** Dashboards are immutable once uploaded; re-saving creates a new object.
