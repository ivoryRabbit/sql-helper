# SQL Helper — AI Collaboration Guide

This file is the entry point for Claude Code sessions working in this repo. It gives the high-level picture.

- **Design**: [ARCHITECTURE.md](ARCHITECTURE.md) (components, layers, data model) and [WORKFLOW.md](WORKFLOW.md) (user journey + per-feature backend flows).
- **Per-area guides**: [backend/CLAUDE.md](backend/CLAUDE.md), [frontend/CLAUDE.md](frontend/CLAUDE.md).
- **Feature specs (PRD)**: [prd/](prd/) — one file per feature, authoritative for DB schema and API contracts.

---

## What this project is

A **text-to-SQL service** with a five-step pipeline: users register data sources, generate a vector catalog of their schemas (and search over it), ask natural-language questions (LLM agent produces SQL), execute + analyze the results, and save HTML dashboards.

```
Data Source → Data Catalog (Browse + Search) → Text-to-SQL → Data Analysis → Dashboard
```

Data Catalog includes both schema browsing and semantic vector search — they were previously separate features but are now unified in a single tab and backend service. Each stage is one backend service, one frontend tab. See [ARCHITECTURE.md](ARCHITECTURE.md) and [WORKFLOW.md](WORKFLOW.md) for details. The PRDs in [prd/](prd/) are the canonical reference for each feature's schema, endpoints, and request/response models.

The final goal of current work is to **port the legacy Streamlit prototype (`legacy/`) to a production-style service**: FastAPI backend + SvelteKit frontend + pgvector for retrieval + MinIO for dashboard storage + Temporal for async catalog generation. The legacy folder is reference-only and will be deleted once the port is complete.

---

## Monorepo layout

| Directory | Purpose |
|---|---|
| [backend/](backend/) | FastAPI + SQLAlchemy async + pgvector. Text-to-SQL engine and API. **Primary area of active development.** `src/` is not yet created — build from scratch following the PRDs and [backend/CLAUDE.md](backend/CLAUDE.md). |
| [frontend/](frontend/) | Svelte 4 + Vite 5 SPA. Will migrate to SvelteKit (see [frontend/CLAUDE.md](frontend/CLAUDE.md)). |
| [legacy/](legacy/) | Old Streamlit demo. **Read-only reference for porting**; do not edit. Will be deleted. |
| [mcp_server/](mcp_server/) | Experimental MCP server (not wired into the main app yet). Separate Chroma-based prototype. |
| [docker/](docker/) | DB init scripts and data volumes. |
| [bin/](bin/) | Dev scripts: [bin/run-backend.sh](bin/run-backend.sh), [bin/run-frontend.sh](bin/run-frontend.sh). |
| [docker-compose.yaml](docker-compose.yaml) | Runs `postgres`, `temporal`, `temporal-ui`, `minio`. Backend and frontend services are defined but commented out (run locally via `bin/` scripts). |
| [prd/](prd/) | Product requirements: schema, endpoints, and implementation details per feature. |

---

## Tech stack

| Layer | Tech | Version |
|---|---|---|
| Backend framework | FastAPI | 0.128.0 |
| ASGI server | Uvicorn | 0.37.0 |
| ORM | SQLAlchemy (async) + SQLModel | 2.0.43 / 0.0.26 |
| DB driver | psycopg (v3, binary) | 3.2.10 |
| Vector | pgvector (SQL extension + Python client) | 0.4.1, `pgvector/pgvector:0.8.1-pg17` image |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384-dim) | 4.1.0 |
| Validation | Pydantic + pydantic-settings | 2.12.5 |
| DI | `dependency-injector` | 4.48.2 |
| Async workflows | Temporal (catalog generation + analysis) | `temporalio` (Python SDK) |
| Object storage | MinIO (S3-compatible, for dashboard HTML + exports) | `minio/minio:latest` |
| LLM provider | OpenAI (primary); pluggable for Claude/local | — |
| Frontend framework | Svelte 4 → **target: SvelteKit** | 4.2.0 |
| Frontend build | Vite | 5.2.0 |
| Python | 3.11 (Dockerfile) | — |

---

## Local dev workflow

```bash
# 1. Start Postgres + pgvector (only service wired today)
docker compose up -d postgres

# 2. Backend (port 8000)
./bin/run-backend.sh
# internally: uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir src --reload

# 3. Frontend (port 3000)
./bin/run-frontend.sh
```

Target full-stack docker-compose (when all services are wired):
- Postgres: `postgresql://sqlhelper:sqlhelper@0.0.0.0:5432/vectordb`, schema `data_catalog`
- Temporal: `temporal:7233` (workflow orchestration)
- Temporal UI: `http://localhost:8088` (monitoring)
- MinIO: `http://localhost:9000` (S3), `http://localhost:9001` (console)
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

Backend reads all config from env vars (see [backend/src/configs/settings.py](backend/src/configs/settings.py) once created). Key vars: `DATABASE_URL`, `TEMPORAL_ADDRESS`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `OPENAI_API_KEY`.

---

## Architecture in one diagram

```
┌────────────┐    HTTP/JSON + SSE     ┌─────────────────────────────────────────────────┐
│  SvelteKit │ ─────────────────────▶ │  FastAPI  (backend/src)                         │
└────────────┘                         │                                                 │
                                       │  controllers → services →                       │
                                       │  repositories → DatabaseManager                 │
                                       │            │                                    │
                                       │            ▼                                    │
                                       │  ┌────────────────────────────┐                 │
                                       │  │ Postgres + pgvector        │                 │
                                       │  │  schema: data_catalog      │                 │
                                       │  │  (see DB schema below)     │                 │
                                       │  └────────────────────────────┘                 │
                                       │            │                                    │
                                       │            ▼                                    │
                                       │  ┌──────────────┐  ┌──────────────────────┐    │
                                       │  │  Temporal    │  │  MinIO (S3)          │    │
                                       │  │  (workflows) │  │  (dashboard HTML +   │    │
                                       │  └──────────────┘  │   exports)           │    │
                                       │                     └──────────────────────┘    │
                                       │                                                 │
                                       │  LLM API (OpenAI / Claude — pluggable)          │
                                       └─────────────────────────────────────────────────┘
```

---

## Complete database schema

All tables live in the `data_catalog` schema. See PRDs for full DDL.

| Table | Feature | Purpose |
|---|---|---|
| `data_sources` | 1 | Registered DB connections (PostgreSQL, Redshift, Trino) |
| `schemas` | 2 | Schema names per data source |
| `tables` | 2 | Table/view metadata per schema |
| `columns` | 2 | Column metadata per table |
| `table_documents` | 2 | Vector embeddings for semantic search (`ddl`\|`doc`\|`example`) |
| `search_history` | 2 | User semantic search query log |
| `sql_generations` | 3 | LLM-generated SQL with validation status |
| `analysis_executions` | 4 | SQL execution records and status |
| `analysis_results` | 4 | Per-column statistics from executed queries |
| `analysis_insights` | 4 | Auto-generated data insights |
| `dashboards` | 5 | Dashboard configurations and HTML |
| `dashboard_widgets` | 5 | Individual widget configs per dashboard |

Key invariants:
- `table_documents.document_type` is a discriminator: `ddl` | `doc` | `example` — don't create separate tables.
- `table_documents.embedding` is 384-dim VECTOR for `all-MiniLM-L6-v2`.
- `data_sources.config` stores connection config as JSONB with encrypted sensitive fields.

---

## API surface (target)

```
# Feature 1 — Data Source
POST/GET/PUT/DELETE  /api/v1/data-sources
POST                 /api/v1/data-sources/{id}/test
POST                 /api/v1/data-sources/{id}/sync

# Feature 2 — Data Catalog (Browse + Semantic Search, merged)
GET    /api/v1/data-catalog/sources/{id}
GET    /api/v1/data-catalog/tables
GET    /api/v1/data-catalog/tables/{id}
GET    /api/v1/data-catalog/schemas
GET    /api/v1/data-catalog/search
POST   /api/v1/data-catalog/refresh
GET    /api/v1/data-catalog/stats
POST   /api/v1/data-catalog/semantic-search
POST   /api/v1/data-catalog/similar
GET    /api/v1/data-catalog/recommendations
GET    /api/v1/data-catalog/history

# Feature 3 — SQL Assistant (generate is streaming SSE)
POST   /api/v1/sql-assistant/generate
POST   /api/v1/sql-assistant/validate
POST   /api/v1/sql-assistant/explain
POST   /api/v1/sql-assistant/optimize
GET    /api/v1/sql-assistant/history

# Feature 4 — Data Analysis
POST   /api/v1/data-analysis/execute
POST   /api/v1/data-analysis/analyze
GET    /api/v1/data-analysis/results/{id}
GET    /api/v1/data-analysis/history
POST   /api/v1/data-analysis/export

# Feature 5 — Dashboard
POST/GET/PUT/DELETE  /api/v1/dashboards
POST/PUT/DELETE      /api/v1/dashboards/{id}/widgets/{widget_id}
GET                  /api/v1/dashboards/{id}/html
POST                 /api/v1/dashboards/{id}/share
```

---

## Cross-cutting conventions

- **Async all the way** on backend — every controller, service, repo method is `async def`; use `AsyncSession`, never sync Session.
- **Pydantic** for all request/response schemas; **SQLAlchemy** `Mapped[...]` entities live in `backend/src/models/entities.py`.
- **DI** via `dependency-injector` in `backend/src/configs/container.py`. Wire new providers through `AppContainer`.
- **Streaming** for SQL Assistant responses: `POST /sql-assistant/generate` returns `StreamingResponse` (SSE). Preserve this when wiring the real LLM.
- **Temporal** for long-running background jobs: catalog sync, LLM processing, analysis workflows.
- **MinIO** for blob storage: dashboard HTML exports, CSV/JSON/Excel exports.
- **Docs in English**; code identifiers in English; user-facing UI strings may be Korean.
- **Formatting**: follow surrounding style; no blanket reformats.

---

## Legacy → Backend port roadmap

The legacy `SQLAgent` orchestrates a RAG pipeline we need to rebuild in the async backend. Map:

| Legacy (`legacy/`) | New home (`backend/`) | Notes |
|---|---|---|
| [legacy/src/core/sql_agent.py](legacy/src/core/sql_agent.py) — `SQLAgent.generate_sql`, `is_sql_valid`, `generate_followup_questions`, `generate_suggestions`, `extract_sql` | `backend/src/services/sql_assistant.py` (new) | Async rewrite. Keep the pipeline: retrieve DDL → retrieve docs → retrieve Q/SQL examples → build prompt → LLM stream → `extract_sql` → `sqlparse`-based validation. |
| [legacy/src/core/vector_store/chromadb.py](legacy/src/core/vector_store/chromadb.py), pgvector.py, qdrant.py | `backend/src/repositories/table_document.py` (new) | One table `table_documents` with `document_type` discriminator. Don't introduce new tables. |
| [legacy/src/core/assistant/](legacy/src/core/assistant/) (OpenAI/Cohere/Claude clients) | `backend/src/clients/llm.py` (new) | Async. Start with OpenAI only; pluggable via `ai_models` setting surfaced in frontend. |
| Streamlit chat history (`collections.deque` in legacy/src/client/page/chat.py) | Frontend-local state in `src/routes/query/+page.svelte` | Backend stays stateless; the client passes conversation context in each request. |
| `legacy/src/core/` schema analysis | `backend/src/services/data_catalog.py` + Temporal workflow | Schema discovery runs as a Temporal workflow for async reliability. |
| MovieLens Trino data loader | Keep as reference; `mcp_server/data_loader.py` is closer to target | Port only when Trino is wired as a real data-source type. |

When implementing a piece of this roadmap, open the legacy file, read it, then design the async version — don't blindly copy sync code.

---

## What NOT to do

- **Don't edit anything in `legacy/`.** Reference only.
- **Don't mock pgvector or the DB in tests** — use a real test DB (integration over unit for RAG paths).
- **Don't commit `.env`** (only `.env.example` is tracked).
- **Don't call external LLM APIs from tests** — inject a fake assistant.
- **Don't add new `table_documents`-like tables** for DDL/doc/example stores; reuse the `document_type` discriminator.
- **Don't introduce UI component libraries / Tailwind** without discussion — the frontend is deliberately minimal right now.

---

## Current state (as of 2026-05)

- **Backend Features 1–3 complete.** `src/` exists with Data Source, Data Catalog, and Data Discovery backends implemented. Next: Feature 4 Text-to-SQL.
- **PRDs are the authoritative spec**: [prd/0_infra.md](prd/0_infra.md) through [prd/5_dashboard.md](prd/5_dashboard.md) define the full DB schema, API contracts, and implementation patterns.
- **docker-compose.yaml** runs `postgres`, `temporal`, `temporal-ui`, and `minio`. Backend and frontend still run locally via `bin/` scripts.
- **Frontend** is a functional single-file SPA (Svelte 4); migration to SvelteKit is pending. Features 1–3 frontend shells exist but are not yet wired to real APIs.
- `mcp_server/` is an unfinished side-experiment; not part of the main backend.
- **Feature 2 (Catalog) and Feature 3 (Discovery) are merged**: backend `DataCatalogService` handles both browse and semantic search; frontend uses a single `DataCatalog.svelte` component with Browse/Search tabs.
- Implementation order follows the pipeline: Feature 1 (Data Source) → 2 (Catalog + Search) → 3 (Text-to-SQL) → 4 (Analysis) → 5 (Dashboard).
