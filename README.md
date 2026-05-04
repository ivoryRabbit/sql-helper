<div align="center">

# SQL Helper

**Ask questions in natural language. Get SQL back instantly.**

A production-style text-to-SQL service — register your databases, explore schemas with semantic search, and let an LLM agent write and analyze SQL for you. Supports **English, Korean**, and more.

[한국어 README](README_ko.md)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Svelte](https://img.shields.io/badge/Svelte-4-FF3E00?logo=svelte&logoColor=white)](https://svelte.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-0.8.1-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Temporal](https://img.shields.io/badge/Temporal-workflow-000000?logo=temporal&logoColor=white)](https://temporal.io)
[![MinIO](https://img.shields.io/badge/MinIO-S3-C72E49?logo=minio&logoColor=white)](https://min.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

</div>

---

## How it works

```
Data Source  →  Data Catalog  →  SQL Assistant  →  Data Analysis  →  Dashboard
  Register       Browse &          LLM generates     Execute &          Save &
 connections    vector search      streaming SQL     auto-insights      share HTML
```

Type a question like *"Show me the top 10 customers by revenue last quarter"* — SQL Helper retrieves relevant schema context via pgvector, feeds it to the LLM, streams SQL back token-by-token, executes it, and renders a shareable dashboard widget.

---

## Features

| # | Feature | Status |
|---|---|---|
| 1 | **Data Source** — connect PostgreSQL, Redshift, or Trino | ✅ |
| 2 | **Data Catalog** — browse schemas and run semantic vector search | ✅ |
| 3 | **SQL Assistant** — LLM text-to-SQL with real-time streaming (SSE) | ✅ |
| 4 | **Data Analysis** — execute SQL, auto-generate stats and insights | ✅ |
| 5 | **Dashboard** — save and share HTML dashboards via MinIO | ✅ |

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI 0.128 · SQLAlchemy 2.0 async · psycopg v3 |
| Vector search | pgvector · `all-MiniLM-L6-v2` (384-dim embeddings) |
| Async workflows | Temporal (catalog sync, analysis pipelines) |
| Object storage | MinIO — S3-compatible (dashboard HTML + CSV exports) |
| LLM | OpenAI · Google Gemini (pluggable via `LLM_PROVIDER`) |
| Frontend | Svelte 4 · Vite 5 |
| Database | PostgreSQL 17 + pgvector 0.8.1 |
| DI | dependency-injector · Pydantic settings |

---

## Quick Start

**Prerequisites:** Docker, Python 3.11+, Node.js 20+

### Option A — Full Docker stack

```bash
cp .env.example .env          # fill in OPENAI_API_KEY or GOOGLE_API_KEY
docker compose up -d
```

### Option B — Local dev (hot-reload)

```bash
cp .env.example .env

# Infrastructure only
docker compose up -d postgres temporal minio

# Backend  →  http://localhost:8000
./bin/run-backend.sh

# Temporal worker (separate terminal)
cd backend && python src/worker.py

# Frontend  →  http://localhost:3000
./bin/run-frontend.sh
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Temporal UI | http://localhost:8088 |
| MinIO Console | http://localhost:9001 |

---

## LLM Providers

Set `LLM_PROVIDER` in `.env` to switch:

| Provider | `LLM_PROVIDER` | Key |
|---|---|---|
| OpenAI (default) | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` |

---

## Project Structure

```
backend/    FastAPI app — controllers, services, repositories, Temporal workflows
frontend/   Svelte 4 SPA
docker/     DB init scripts
bin/        Dev run scripts
prd/        Feature specs (DB schema + API contracts per feature)
legacy/     Original Streamlit prototype (reference only, will be removed)
```

---

## Architecture

```
SvelteKit ──HTTP/SSE──▶ FastAPI
                           │
                    controllers → services → repositories
                           │
                     PostgreSQL + pgvector
                           │
                   Temporal ──▶ MinIO
                           │
                      LLM API (OpenAI / Gemini)
```

All backend code is async end-to-end. Long-running jobs (catalog generation, analysis) run as Temporal workflows. Dashboard HTML and CSV exports are stored in MinIO.
