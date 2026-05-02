---
name: prd-guide
description: This skill should be used when the user asks to "write a PRD", "create a PRD", "PRD 작성", "요구사항 문서 작성", "제품 요구사항 정의", or needs to define API contracts, DB schema, and implementation specs for a new feature.
---

# PRD 작성 가이드

PRD는 `prd/` 디렉토리에 `{N}_{feature}.md` 형식으로 작성한다 (예: `0_infra.md`, `1_data_source.md`).

## 문서 구조 템플릿

```markdown
# [기능명] (Feature N)

## Overview
## API Endpoints
## Request/Response Models
## Database Schema
## Implementation Details
## Integration Points
## Security Considerations
```

## 핵심 원칙

- **명확성**: 정량적 요구사항 사용 ("응답 200ms 이하", not "빠른 성능")
- **단일 책임**: 파일 하나에 기능 하나
- **구현 가능성**: 실제 스택(FastAPI + SQLAlchemy async + pgvector) 기준으로 작성
- **영어 식별자**: API path, 필드명, 타입은 영어; 설명은 한국어 허용

## DB 스키마 작성 시

- 모든 테이블은 `data_catalog` 스키마에 위치
- `table_documents`에 새 타입 추가 시 `document_type` discriminator 활용 (새 테이블 금지)
- embedding은 384-dim `VECTOR` (`all-MiniLM-L6-v2`)

## API 설계 시

- RESTful + `/api/v1/` prefix 유지
- 목록 조회에는 페이지네이션 포함 (`page`, `limit`, `total`, `has_next`)
- 스트리밍이 필요한 엔드포인트는 SSE 방식 명시

자세한 작성 패턴과 예시는 [references/prd-writing-guide.md](references/prd-writing-guide.md)를 참고한다.
