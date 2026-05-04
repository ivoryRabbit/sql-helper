---
name: be-work
description: This skill should be used when the user asks to "work on the backend", "implement a backend feature", "add an API endpoint", "build the FastAPI service", "백엔드 작업", or invokes /be-work.
---

# Backend Work

Operate exclusively in `backend/`. Do not touch `frontend/`, `legacy/`, or `mcp_server/` unless reading `legacy/` as a porting reference.

## Before starting any task

Read these files in order:
1. [CLAUDE.md](../../../CLAUDE.md) — project-wide context, tech stack, DB schema, API surface
2. [backend/CLAUDE.md](../../../backend/CLAUDE.md) — target directory layout, layer responsibilities, coding conventions
3. [WORKFLOW.md](../../../WORKFLOW.md) — per-feature backend flows, current implementation status, and next priorities
4. The relevant PRD under [prd/](../../../prd/) for the feature being implemented

## Conventions

- **Async all the way**: every controller / service / repository method must be `async def`. Never use sync `Session`.
- **Layer boundaries**: controllers handle HTTP only; services hold business logic; repositories own DB access.
- **DI via dependency-injector**: wire new components through `AppContainer` in `backend/src/configs/container.py`.
- **Pydantic** for all request/response schemas. **SQLAlchemy `Mapped[...]`** entities in `backend/src/models/entities.py`.
- **pgvector** for embeddings — `table_documents` table, `document_type` discriminator (`ddl` | `doc` | `example`), 384-dim vector.
- **Temporal** for long-running jobs (catalog sync, analysis). Do not run these inline.
- **MinIO** for blob storage (dashboard HTML, exports).
- **Streaming** for `/text-to-sql/generate`: return `StreamingResponse` (SSE).
- **No mocking the DB in tests** — use a real test DB; inject a fake assistant for LLM calls.
- **English** identifiers and docs; add comments only when the WHY is non-obvious.

## What NOT to do

- Do not edit anything in `legacy/` — read-only reference only.
- Do not add new tables for DDL/doc/example stores — reuse the `document_type` discriminator.
- Do not commit `.env`.
- Do not call real LLM APIs from tests.
- Do not deviate from the target layout defined in `backend/CLAUDE.md`.

## Current state

`backend/src/` does not yet exist. Build from scratch per the PRDs and `backend/CLAUDE.md`. Implementation order: Feature 1 (Data Source) → 2 (Catalog + Search) → 3 (Text-to-SQL) → 4 (Analysis) → 5 (Dashboard).
