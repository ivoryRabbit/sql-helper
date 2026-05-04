<div align="center">

# SQL Helper

**한국어로 질문하면 SQL이 바로 나옵니다.**

데이터베이스를 등록하고, 스키마를 시맨틱 검색으로 탐색하고, LLM 에이전트가 자연어 질문을 SQL로 변환해줍니다. **한국어, 영어** 등 다국어 질문을 지원합니다.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Svelte](https://img.shields.io/badge/Svelte-4-FF3E00?logo=svelte&logoColor=white)](https://svelte.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-0.8.1-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Temporal](https://img.shields.io/badge/Temporal-workflow-000000?logo=temporal&logoColor=white)](https://temporal.io)
[![MinIO](https://img.shields.io/badge/MinIO-S3-C72E49?logo=minio&logoColor=white)](https://min.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[English README](README.md)

</div>

---

## 동작 방식

```
데이터 소스  →  데이터 카탈로그  →  SQL 어시스턴트  →  데이터 분석  →  대시보드
  연결 등록      스키마 탐색 &       LLM이 SQL 생성      실행 &           저장 &
               시맨틱 벡터 검색      (실시간 스트리밍)   자동 인사이트     HTML 공유
```

*"지난 분기 매출 상위 10명 고객을 보여줘"* 처럼 자연어로 질문하면 — SQL Helper가 pgvector로 관련 스키마 컨텍스트를 검색하고, LLM에 전달해 SQL을 토큰 단위로 스트리밍하며, 실행 결과를 분석해 공유 가능한 대시보드 위젯으로 렌더링합니다.

---

## 기능

| # | 기능 | 상태 |
|---|---|---|
| 1 | **데이터 소스** — PostgreSQL, Redshift, Trino 연결 등록 | ✅ |
| 2 | **데이터 카탈로그** — 스키마 탐색 및 시맨틱 벡터 검색 | ✅ |
| 3 | **SQL 어시스턴트** — LLM 텍스트-to-SQL, 실시간 스트리밍(SSE) | ✅ |
| 4 | **데이터 분석** — SQL 실행, 통계 및 인사이트 자동 생성 | ✅ |
| 5 | **대시보드** — MinIO를 통한 HTML 대시보드 저장 및 공유 | ✅ |

---

## 기술 스택

| 레이어 | 기술 |
|---|---|
| 백엔드 | FastAPI 0.128 · SQLAlchemy 2.0 async · psycopg v3 |
| 벡터 검색 | pgvector · `all-MiniLM-L6-v2` (384차원 임베딩) |
| 비동기 워크플로우 | Temporal (카탈로그 동기화, 분석 파이프라인) |
| 오브젝트 스토리지 | MinIO — S3 호환 (대시보드 HTML + CSV 내보내기) |
| LLM | OpenAI · Google Gemini · Anthropic Claude (`LLM_PROVIDER`로 전환 가능) |
| 프론트엔드 | Svelte 4 · Vite 5 |
| 데이터베이스 | PostgreSQL 17 + pgvector 0.8.1 |
| DI | dependency-injector · Pydantic settings |

---

## 빠른 시작

**사전 준비:** Docker, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node.js 20+

### Option A — 전체 Docker 스택

```bash
cp .env.example .env          # OPENAI_API_KEY, GOOGLE_API_KEY 또는 ANTHROPIC_API_KEY 입력
docker compose up -d
```

### Option B — 로컬 개발 환경 (hot-reload)

```bash
cp .env.example .env

# 인프라만 실행
docker compose up -d postgres temporal minio

# 백엔드 — 의존성 설치 후 실행 (http://localhost:8000)
cd backend && uv sync --dev    # .venv 생성 및 전체 의존성 설치
cd ..
./bin/run-backend.sh

# Temporal 워커 (별도 터미널)
cd backend && uv run python src/worker.py

# 프론트엔드  →  http://localhost:3000
./bin/run-frontend.sh
```

API 문서: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 서비스 URL

| 서비스 | URL |
|---|---|
| 프론트엔드 | http://localhost:3000 |
| 백엔드 API | http://localhost:8000 |
| Temporal UI | http://localhost:8088 |
| MinIO 콘솔 | http://localhost:9001 |

---

## LLM 프로바이더

`.env`의 `LLM_PROVIDER`를 변경해 LLM을 전환할 수 있습니다:

| 프로바이더 | `LLM_PROVIDER` | 필요한 키 |
|---|---|---|
| OpenAI (기본값) | `openai` | `OPENAI_API_KEY` |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` |
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |

---

## 프로젝트 구조

```
backend/    FastAPI 앱 — 컨트롤러, 서비스, 레포지토리, Temporal 워크플로우
frontend/   Svelte 4 SPA
docker/     DB 초기화 스크립트
bin/        개발용 실행 스크립트
prd/        기능 명세 (DB 스키마 + API 계약)
legacy/     기존 Streamlit 프로토타입 (참고용, 삭제 예정)
```

---

## 아키텍처

```
SvelteKit ──HTTP/SSE──▶ FastAPI
                           │
                    컨트롤러 → 서비스 → 레포지토리
                           │
                     PostgreSQL + pgvector
                           │
                   Temporal ──▶ MinIO
                           │
                      LLM API (OpenAI / Gemini / Claude)
```

백엔드 코드는 전체가 async로 구성되어 있습니다. 카탈로그 생성, 분석 등 장기 실행 작업은 Temporal 워크플로우로 처리하며, 대시보드 HTML과 CSV 내보내기는 MinIO에 저장됩니다.
