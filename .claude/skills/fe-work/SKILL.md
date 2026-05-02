---
name: fe-work
description: This skill should be used when the user asks to "work on the frontend", "implement a frontend feature", "update the UI", "build a Svelte component", "fix the frontend", "프론트엔드 작업", or invokes /fe-work.
---

# Frontend Work

Operate exclusively in `frontend/`. Do not touch `backend/`, `legacy/`, or `mcp_server/`.

## Before starting any task

Read these files in order:
1. [CLAUDE.md](../../../CLAUDE.md) — project-wide context, API surface, data flow
2. [frontend/CLAUDE.md](../../../frontend/CLAUDE.md) — layout, component structure, UI conventions

## Tech stack

| | |
|---|---|
| Framework | Svelte 4 (do **not** migrate to SvelteKit unless explicitly asked) |
| Build | Vite 5 |
| Language | TypeScript |
| Styling | Plain CSS — no Tailwind, no component libraries without discussion |

## Layout contract

```
App Bar (header)
├── Nav Sidebar (200 px, sticky)       — page/feature navigation
├── Conversation View (flex: 1)        — message bubbles + prompt input bar
└── Session Panel (260 px)             — session history list
```

- Backend is at `http://localhost:8000`. Direct all API calls there.
- Text-to-SQL generate endpoint (`POST /api/v1/text-to-sql/generate`) streams SSE — handle with `EventSource` or `fetch` + `ReadableStream`.
- Chat history is **frontend-local state** (not persisted to the backend). Pass conversation context in each request body.

## Conventions

- **No UI component libraries or Tailwind** without explicit approval — keep it minimal.
- **Typed fetch wrappers** — define request/response types matching the PRD models.
- **Svelte stores** for shared state (active session, data source selection).
- **Accessible markup** — use semantic HTML elements (`<header>`, `<nav>`, `<main>`, `<aside>`).
- **User-facing strings may be Korean**; code identifiers and comments in English.
- Test the golden path and edge cases in a browser before marking a task done. Start the dev server with `./bin/run-frontend.sh` (port 3000).

## What NOT to do

- Do not introduce SvelteKit routing or SSR patterns.
- Do not add Tailwind, component libraries, or icon packs without discussion.
- Do not store conversation history in the backend — keep it in frontend state.
- Do not call backend endpoints that do not yet exist in the API surface (check `CLAUDE.md`).
