# PRD 상세 작성 가이드

## 요구사항 정리 방법

### 기능 분해

1. **핵심 기능(Core Features)** — MVP 범위, 반드시 필요한 기능
2. **확장 기능(Extended Features)** — 경쟁 우위 및 UX 향상 기능
3. **기술적 요구사항(Technical Requirements)** — 성능, 확장성, 보안

### 우선순위 매트릭스 예시

| 기능 | 사용자 가치 | 구현 난이도 | 우선순위 |
|------|------------|------------|----------|
| 데이터 소스 연동 | 높음 | 중간 | 1 |
| SQL 생성 | 높음 | 높음 | 2 |
| 대시보드 | 중간 | 높음 | 3 |

---

## API 설계 패턴

### 목록 조회 (페이지네이션 포함)

```
GET /api/v1/data-sources?page=1&limit=20&type=postgresql
```

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "has_next": true
  }
}
```

### SSE 스트리밍 엔드포인트

```
POST /api/v1/text-to-sql/generate
Content-Type: application/json

→ Response: text/event-stream
data: {"type": "token", "content": "SELECT"}
data: {"type": "done", "sql": "SELECT ..."}
```

---

## DB 스키마 작성 패턴

```sql
CREATE TABLE data_catalog.data_sources (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    type        VARCHAR(50)  NOT NULL CHECK (type IN ('postgresql', 'redshift', 'trino')),
    config      JSONB        NOT NULL,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_data_sources_type ON data_catalog.data_sources(type);
```

### table_documents discriminator 패턴

새 문서 유형 추가 시 테이블을 새로 만들지 않고 `document_type` 값을 추가한다.

```sql
-- document_type: 'ddl' | 'doc' | 'example'  (기존 값 재사용)
INSERT INTO data_catalog.table_documents (table_id, document_type, content, embedding)
VALUES (:table_id, 'doc', :content, :embedding);
```

---

## 검증 가능한 요구사항 작성

| 나쁜 예 | 좋은 예 |
|--------|--------|
| "빠른 성능" | "API 응답 시간 평균 200ms 이하 (p95 500ms)" |
| "많은 사용자 지원" | "동시 사용자 100명 처리 가능" |
| "대용량 데이터" | "10만 건 조회 시 3초 이내" |

---

## PRD 품질 체크리스트

- [ ] 목표와 범위가 명확한가?
- [ ] API path, 필드명이 영어로 일관되게 정의되었는가?
- [ ] 요구사항이 정량적으로 표현되었는가?
- [ ] DB 스키마가 `data_catalog` 스키마 내에 위치하는가?
- [ ] 다른 기능과의 의존성이 명시되었는가?
- [ ] 보안 고려사항(인증, 입력 검증, 민감 정보 처리)이 포함되었는가?

---

## 흔한 실수

- **과도한 구현 상세**: PRD는 "무엇을"이지 "어떻게"가 아님 — 코드 수준 상세는 `backend/CLAUDE.md`로
- **모호한 표현**: "빠름", "쉬움" 등 정량 불가 표현 금지
- **누락된 에지 케이스**: 예외 상황과 에러 응답 포맷 명시
- **비현실적 요구사항**: 현재 스택(FastAPI + pgvector + Temporal)의 제약 고려
