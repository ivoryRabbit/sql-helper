# Backend — AI Collaboration Guide

FastAPI + SQLAlchemy async + pgvector. See [../CLAUDE.md](../CLAUDE.md) for the project-wide picture and [../prd/](../prd/) for authoritative feature specs (DB schema, endpoints, request/response models).

> **Current state** (2026-05-02): `src/` exists with Features 1–3 backend complete. Infrastructure clients (MinIO, Temporal) wired. Next: Feature 4 Text-to-SQL.

---

## Target directory layout

```
backend/
├── src/
│   ├── main.py                     — FastAPI app factory, lifespan (DB + Temporal init), CORS, router registration
│   ├── worker.py                   — Temporal worker entry point (registers workflows + activities)
│   ├── components/
│   │   └── database_manager.py     — AsyncEngine + async_scoped_session + pgvector ModelBase
│   ├── configs/
│   │   ├── settings.py             — Pydantic Settings (env-driven: DB, Temporal, MinIO, OpenAI)
│   │   ├── container.py            — dependency-injector AppContainer
│   │   └── routers.py              — register_routers(app)
│   ├── controllers/                — FastAPI routers (HTTP layer only — no business logic)
│   │   ├── data_source.py
│   │   ├── data_catalog.py         — browse + semantic search endpoints (merged Feature 2+3)
│   │   ├── sql_assistant.py
│   │   ├── data_analysis.py
│   │   ├── dashboard.py
│   │   ├── ping.py
│   │   └── home.py
│   ├── services/                   — Business logic, orchestration, LLM/RAG pipelines
│   │   ├── data_source.py
│   │   ├── data_catalog.py         — catalog refresh (Temporal) + semantic search methods
│   │   ├── sql_assistant.py        — SQLAgent async rewrite (RAG → LLM → stream → validate)
│   │   ├── data_analysis.py
│   │   └── dashboard.py
│   ├── repositories/               — DB access (generic BaseRepository + entity-specific)
│   │   ├── base.py
│   │   ├── data_source.py
│   │   ├── table_document.py       — pgvector cosine search on table_documents
│   │   ├── catalog.py              — schemas / tables / columns
│   │   ├── sql_generation.py
│   │   ├── analysis.py
│   │   └── dashboard.py
│   ├── clients/
│   │   ├── llm.py                  — Async OpenAI client; pluggable for Claude/local  ✅
│   │   ├── embedding.py            — sentence-transformers all-MiniLM-L6-v2           ✅
│   │   ├── storage.py              — MinIO S3 client (dashboard HTML + exports)       ✅
│   │   └── temporal.py             — Temporal client wrapper (workflow dispatch)       ✅
│   ├── adapters/                   — DB connectors per data-source type
│   │   ├── postgres.py
│   │   ├── redshift.py
│   │   └── trino.py
│   ├── workflows/                  — Temporal workflow definitions
│   │   ├── catalog_sync.py
│   │   └── analysis_execution.py
│   ├── activities/                 — Temporal activity implementations
│   │   ├── catalog.py
│   │   └── analysis.py
│   ├── models/
│   │   ├── entities.py             — SQLAlchemy ORM entities (all tables)
│   │   ├── dto/                    — Internal data-transfer objects (e.g., TableDocument)
│   │   ├── request/
│   │   │   ├── data_catalog.py     — CatalogRefreshRequest, SemanticSearchRequest, SimilarTableRequest
│   │   │   └── ...
│   │   └── response/
│   │       ├── data_catalog.py     — TableResponse, SemanticSearchResponse, RecommendationResponse, ...
│   │       └── ...
│   └── __init__.py
├── test/                           — Integration tests (hit real DB)
├── requirements.txt
└── Dockerfile                      — Python 3.11, uvicorn on :8000
```

---

## Request lifecycle

```
HTTP request
    │
    ▼
controllers/<name>.py           — validates input via Pydantic, returns response schema
    │
    ▼
services/<name>.py              — orchestration, LLM calls, multi-repo coordination
    │
    ▼
repositories/<name>.py          — CRUD on one entity; uses AsyncSession
    │
    ▼
components/database_manager.py  — engine, session factory
    │
    ▼
Postgres (schema=data_catalog)
```

Controllers never call repositories directly. Repositories never call LLMs or other services.

---

## Dependency injection

`AppContainer` is declarative (see `src/configs/container.py`):

- `database_settings` — `DatabaseSettings` (loaded from env).
- `database_manager` — `Singleton(DatabaseManager, ...)`.
- `session` — `Resource(database_manager.provided.session)`.
- `llm_client` — `Singleton(LLMClient, api_key=...)`.
- `storage_client` — `Singleton(MinIOClient, ...)`.

**Adding a new service**:

1. Create `services/<name>.py` with an `async` class taking dependencies in `__init__`.
2. Add a provider to `AppContainer`:
   ```python
   <name>_service = providers.Factory(<Name>Service, session=session)
   ```
3. Wire it into controllers via `Provide[AppContainer.<name>_service]` and add the controller module to `wiring_config.packages`.

---

## Database

- Engine: `postgresql+psycopg` async, created in `DatabaseManager.initialize`.
- Pooling: `pool_size`, `max_overflow`, `pool_recycle` all from `Settings`.
- Sessions: `async_scoped_session` scoped to `asyncio.current_task`. One session per request.
- Schema: everything lives under `data_catalog`. `ModelBase.metadata = MetaData(schema="data_catalog")`.
- Bootstrap: on app startup, `create_tables()` runs `CREATE SCHEMA IF NOT EXISTS data_catalog` + `ModelBase.metadata.create_all`. Initial DDL also lives in [../docker/vectordb/init_db.sql](../docker/vectordb/init_db.sql).

### All entities (`src/models/entities.py`)

| Entity | Key columns |
|---|---|
| `DataSource` | `id, name [unique], type [postgresql\|redshift\|trino], description, config:JSONB, status, last_synced, created_at, updated_at` |
| `Schema` | `id, data_source_id FK, schema_name, created_at` |
| `Table` | `id, schema_id FK, table_name, table_type [table\|view], row_count, description, tags TEXT[], created_at, updated_at` |
| `Column` | `id, table_id FK, column_name, data_type, is_nullable, default_value, is_primary_key, is_foreign_key, references_column, description, ordinal_position` |
| `TableDocument` | `id, document_type [ddl\|doc\|example], schema_name, table_name, column_name, title, content, tags TEXT[], embedding VECTOR(384), created_at, updated_at` |
| `SearchHistory` | `id, query, search_type, results_count, search_time_ms, created_at` |
| `SqlGeneration` | `id, user_query, data_source_id FK, selected_tables UUID[], generated_sql, explanation, confidence_score, llm_model, llm_tokens_used, validation_status [pending\|valid\|invalid], validation_errors TEXT[], created_at` |
| `AnalysisExecution` | `id, sql_generation_id FK, executed_sql, execution_time_ms, row_count, status [running\|completed\|failed], error_message, created_at` |
| `AnalysisResult` | `id, analysis_id FK, column_name, data_type, null_count, unique_count, min_value, max_value, avg_value, summary_stats:JSONB, created_at` |
| `AnalysisInsight` | `id, analysis_id FK, insight_type, insight_text, confidence_score, created_at` |
| `Dashboard` | `id, title, description, layout [grid\|free], is_public, tags TEXT[], html_content, css_content, js_content, created_at, updated_at` |
| `DashboardWidget` | `id, dashboard_id FK, widget_type [chart\|table\|metric\|text], title, position_x, position_y, width, height, analysis_id FK, chart_config:JSONB, created_at, updated_at` |

---

## pgvector usage

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` — 384 dims, cosine similarity.
- `table_documents.document_type` discriminator values: `ddl` | `doc` | `example`.
- HNSW index: `CREATE INDEX ... USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`.
- SQLAlchemy query pattern:
  ```python
  stmt = (
      select(TableDocument)
      .where(TableDocument.document_type == "ddl")
      .order_by(TableDocument.embedding.cosine_distance(q_vec))
      .limit(5)
  )
  ```
- **Don't create separate DDL / doc / example tables** — reuse the one `table_documents` table.

---

## Streaming responses

`POST /api/v1/sql-assistant/generate` uses FastAPI's `StreamingResponse` (SSE) to progressively emit generated SQL chunks. The frontend consumes chunks as they arrive. Don't switch to a buffered single-JSON response.

SSE event format (each line): `data: {"type": "sql_chunk", "content": "...", "generation_id": "..."}\n\n`

Final event: `data: {"type": "generation_complete", "generation_id": "...", "validation": {...}}\n\n`

---

## Settings (env vars)

All configuration is loaded via Pydantic `Settings` from environment variables:

```python
# PostgreSQL
DB_HOST=0.0.0.0 / DB_PORT=5432 / DB_USER=sqlhelper / DB_PASSWORD=sqlhelper / DB_NAME=vectordb

# Temporal
TEMPORAL_ADDRESS=localhost:7233     # temporal:7233 in docker-compose

# MinIO
MINIO_ENDPOINT=localhost:9000       # minio:9000 in docker-compose
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# LLM
OPENAI_API_KEY=sk-...

# Misc
ENCRYPTION_KEY=<base64-encoded-32-bytes>
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Copy `.env.example` → `.env` to get started locally.

---

## Temporal workflows

- **CatalogSyncWorkflow**: triggered by `POST /data-sources/{id}/sync`. Introspects the target DB, populates `schemas`, `tables`, `columns`, then generates `table_documents` embeddings.
- **AnalysisExecutionWorkflow**: triggered by `POST /data-analysis/execute` for long-running queries. Stores results in `analysis_executions` + `analysis_results`.
- Worker entry point: `src/worker.py` — run alongside the FastAPI server in development.

---

## MinIO usage

- **Dashboard exports**: rendered HTML stored as `dashboards/{id}.html`.
- **Data exports**: CSV/JSON/Excel from `POST /data-analysis/export` stored as `exports/{analysis_id}.{format}`.
- Client: `minio` Python SDK (async wrapper or sync in a thread pool executor).

---

## Adding an endpoint — checklist

1. **Schemas**: add request/response models under `src/models/request/` and `src/models/response/`.
2. **Entity** (if new persisted data): add to `src/models/entities.py` so `ModelBase.metadata.create_all` picks it up.
3. **Repository**: create `src/repositories/<name>.py` extending the generic `BaseRepository`.
4. **Service**: create `src/services/<name>.py`; inject the repo via DI.
5. **Controller**: create `src/controllers/<name>.py` with `router = APIRouter(prefix="/<name>", tags=["<name>"])`.
6. **Register**: add `app.include_router(<name>.router, prefix="/api/v1")` in `src/configs/routers.py`.
7. **DI wiring**: if the controller uses `Provide[...]`, add its module to `AppContainer.wiring_config.packages`.

---

## Testing

See **[test/CLAUDE.md](test/CLAUDE.md)** for the full guide: fixtures, patterns, pitfalls, SSE testing, pgvector tips.

Quick rules:
- Tests live in `backend/test/` and hit a real Postgres via transaction rollback isolation.
- **Never mock pgvector or the DB** — prior incidents have shown mock/real divergence on vector queries.
- For RAG / LLM logic, **inject `FakeLLMClient`** (`test/fakes/llm.py`) rather than calling OpenAI.
- Don't add `pytest` fixtures that silently start containers — document any Docker prerequisites in the test module docstring.

```bash
docker compose up -d postgres
cd backend && pytest
```

---

## Running locally

```bash
./bin/run-backend.sh
# equivalent to:
#   cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir src --reload
```

Requires Postgres running (`docker compose up -d postgres`). For Temporal workflows, also run `python src/worker.py`.

---

## Common gotchas

- The schema `data_catalog` must exist before tables are created. `DatabaseManager.create_tables()` issues `CREATE SCHEMA IF NOT EXISTS` first — keep that ordering.
- `async_scoped_session` uses `asyncio.current_task` as the scope function. Don't open sessions at import time.
- `ModelBase` must be imported **before** `metadata.create_all` runs — add `from models import entities  # noqa: F401` inside `create_tables()`.
- `pgvector` Python package v0.4.1 API differs from older tutorials — check docs if vector queries behave oddly.
- `DataSource.config` stores JSONB. Encrypt sensitive fields (passwords) before writing; decrypt on read. Do not log decrypted values.
- Temporal client requires a running `temporal` server; guard workflow dispatch with a try/except if Temporal is not yet wired.
