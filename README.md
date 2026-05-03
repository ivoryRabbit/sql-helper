# SQL Helper

A **text-to-SQL service** that lets you register data sources, explore schemas via semantic search, and generate SQL from natural-language questions using an LLM agent.

```
Data Source → Data Catalog (Browse + Search) → Text-to-SQL → Data Analysis → Dashboard
```

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI 0.128 · SQLAlchemy 2.0 (async) · psycopg v3 |
| Vector search | pgvector (`all-MiniLM-L6-v2`, 384-dim) |
| Async workflows | Temporal |
| Object storage | MinIO (S3-compatible) |
| LLM | OpenAI · Gemini (pluggable via `LLM_PROVIDER`) |
| Frontend | Svelte 4 · Vite 5 |
| Database | PostgreSQL 17 + pgvector 0.8.1 |

## Quick Start

**Prerequisites:** Docker, Python 3.11+, Node.js 20+

### Option A — Full Docker stack

```bash
# 1. Copy env config
cp .env.example .env
# fill in OPENAI_API_KEY (or GOOGLE_API_KEY) and other values

# 2. Start everything
docker compose up -d
```

### Option B — Local dev (hot-reload)

```bash
# 1. Copy env config
cp .env.example .env

# 2. Start infrastructure
docker compose up -d postgres temporal minio

# 3. Backend  (http://localhost:8000)
./bin/run-backend.sh

# 4. Temporal worker (separate terminal)
cd backend && python src/worker.py

# 5. Frontend  (http://localhost:3000)
./bin/run-frontend.sh
```

API docs: `http://localhost:8000/docs`

## Services

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| Temporal UI | http://localhost:8088 |
| MinIO Console | http://localhost:9001 |

## LLM Provider

Set `LLM_PROVIDER` in `.env` to switch between providers:

| Provider | `LLM_PROVIDER` | Required key |
|---|---|---|
| OpenAI (default) | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` |

## Project Structure

```
backend/      FastAPI app — controllers, services, repositories, Temporal workflows
frontend/     Svelte 4 SPA
docker/       DB init scripts
bin/          Dev run scripts
prd/          Feature specs (DB schema + API contracts)
legacy/       Original Streamlit prototype (reference only)
```

## Features

| # | Feature | Status |
|---|---|---|
| 1 | Data Source — register PostgreSQL / Redshift / Trino connections | ✅ Done |
| 2 | Data Catalog — browse schemas and semantic vector search | ✅ Done |
| 3 | SQL Assistant — LLM-powered text-to-SQL with streaming SSE | ✅ Done |
| 4 | Data Analysis — execute SQL, auto-generate stats and insights | ✅ Done |
| 5 | Dashboard — save and share HTML dashboards via MinIO | ✅ Done |
