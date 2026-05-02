# Refined FastAPI Code Structure with Domain Separation

## 개선된 도메인별 분리 전략

현재 구조의 문제점:
- 모델이 기능별로 분리되어 있지만 도메인 개념이 부족
- 나중에 비즈니스 로직이 복잡해지면 모델 간 의존성이 복잡해짐
- 레이어 간 경계가 불분명해질 수 있음

## 개선된 디렉토리 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── database.py
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # 공통 도메인 베이스
│   │   │   └── value_objects.py     # 공통 값 객체
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # 데이터베이스 설정
│   │   │   ├── security.py         # 보안 인프라
│   │   │   ├── messaging.py        # 메시징 (Redis 등)
│   │   │   └── storage.py          # 파일 저장 (MinIO 등)
│   │   └── application/
│   │       ├── __init__.py
│   │       ├── base.py             # 애플리케이션 서비스 베이스
│   │       ├── exceptions.py       # 애플리케이션 예외
│   │       └── unit_of_work.py     # 작업 단위 관리
│   │
│   ├── domains/                    # 도메인별 분리
│   │   ├── __init__.py
│   │   ├── datasource/            # 데이터 소스 도메인
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py           # 도메인 모델 (엔티티)
│   │   │   │   ├── value_objects.py   # 값 객체 (DataSourceId, ConnectionConfig 등)
│   │   │   │   ├── repositories.py    # 리포지토리 인터페이스
│   │   │   │   └── services.py        # 도메인 서비스
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── services.py        # 애플리케이션 서비스
│   │   │   │   ├── dto.py            # 데이터 전송 객체
│   │   │   │   └── use_cases.py       # 유스케이스
│   │   │   └── infrastructure/
│   │   │       ├── __init__.py
│   │   │       ├── repositories.py    # 리포지토리 구현
│   │   │       ├── connectors.py      # DB 커넥터
│   │   │       └── mappers.py         # 객체-DB 매핑
│   │   │
│   │   ├── catalog/               # 데이터 카탈로그 도메인
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── models.py           # Schema, Table, Column 엔티티
│   │   │   │   ├── value_objects.py   # TableId, ColumnId 등
│   │   │   │   ├── repositories.py    # 카탈로그 리포지토리
│   │   │   │   └── services.py        # 스키마 동기화 서비스
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── services.py        # 카탈로그 애플리케이션 서비스
│   │   │   │   ├── dto.py            # 카탈로그 DTO
│   │   │   │   └── use_cases.py       # 스키마 분석 유스케이스
│   │   │   └── infrastructure/
│   │   │       ├── __init__.py
│   │   │       ├── repositories.py    # 카탈로그 리포지토리 구현
│   │   │       ├── analyzers.py       # 스키마 분석기
│   │   │       └── indexers.py       # 인덱스 생성기
│   │   │
│   │   ├── discovery/             # 데이터 발견 도메인
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── models.py           # Document, Embedding 엔티티
│   │   │   │   ├── value_objects.py   # DocumentId, EmbeddingVector 등
│   │   │   │   ├── repositories.py    # 검색 리포지토리
│   │   │   │   └── services.py        # 임베딩 생성 서비스
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── services.py        # 검색 애플리케이션 서비스
│   │   │   │   ├── dto.py            # 검색 DTO
│   │   │   │   └── use_cases.py       # 의미 검색 유스케이스
│   │   │   └── infrastructure/
│   │   │       ├── __init__.py
│   │   │       ├── repositories.py    # 검색 리포지토리 구현
│   │   │       ├── embeddings.py      # 임베딩 생성기
│   │   │       └── vector_search.py   # 벡터 검색 엔진
│   │   │
│   │   ├── texttosql/             # Text-to-SQL 도메인
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── models.py           # SQLGeneration 엔티티
│   │   │   │   ├── value_objects.py   # Query, GeneratedSQL 등
│   │   │   │   ├── repositories.py    # SQL 생성 리포지토리
│   │   │   │   └── services.py        # SQL 검증 서비스
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── services.py        # SQL 생성 애플리케이션 서비스
│   │   │   │   ├── dto.py            # SQL 생성 DTO
│   │   │   │   └── use_cases.py       # SQL 생성 유스케이스
│   │   │   └── infrastructure/
│   │   │       ├── __init__.py
│   │   │       ├── repositories.py    # SQL 생성 리포지토리 구현
│   │   │       ├── llm_clients.py    # LLM 클라이언트
│   │   │       └── validators.py      # SQL 검증기
│   │   │
│   │   ├── analysis/              # 데이터 분석 도메인
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── models.py           # Analysis, Insight 엔티티
│   │   │   │   ├── value_objects.py   # AnalysisId, Statistics 등
│   │   │   │   ├── repositories.py    # 분석 리포지토리
│   │   │   │   └── services.py        # 통계 분석 서비스
│   │   │   ├── application/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── services.py        # 분석 애플리케이션 서비스
│   │   │   │   ├── dto.py            # 분석 DTO
│   │   │   │   └── use_cases.py       # 분석 실행 유스케이스
│   │   │   └── infrastructure/
│   │   │       ├── __init__.py
│   │   │       ├── repositories.py    # 분석 리포지토리 구현
│   │   │       ├── executors.py       # 쿼리 실행기
│   │   │       └── analyzers.py       # 데이터 분석기
│   │   │
│   │   └── dashboard/             # 대시보드 도메인
│   │       ├── __init__.py
│   │       ├── domain/
│   │       │   ├── models.py           # Dashboard, Widget 엔티티
│   │       │   ├── value_objects.py   # DashboardId, WidgetConfig 등
│   │       │   ├── repositories.py    # 대시보드 리포지토리
│   │       │   └── services.py        # 위젯 관리 서비스
│   │       ├── application/
│   │       │   ├── __init__.py
│   │       │   ├── services.py        # 대시보드 애플리케이션 서비스
│   │       │   ├── dto.py            # 대시보드 DTO
│   │       │   └── use_cases.py       # 대시보드 생성 유스케이스
│   │       └── infrastructure/
│   │           ├── __init__.py
│   │           ├── repositories.py    # 대시보드 리포지토리 구현
│   │           ├── generators.py      # HTML 생성기
│   │           └── renderers.py      # 위젯 렌더러
│   │
│   └── interfaces/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   └── routers/
│       │   │       ├── __init__.py
│       │   │       ├── datasource.py    # 데이터 소스 API 라우터
│       │   │       ├── catalog.py       # 카탈로그 API 라우터
│       │   │       ├── discovery.py     # 발견 API 라우터
│       │   │       ├── texttosql.py     # Text-to-SQL API 라우터
│       │   │       ├── analysis.py      # 분석 API 라우터
│       │   │       └── dashboard.py     # 대시보드 API 라우터
│       │   └── dependencies.py          # API 의존성
│       └── cli/                     # CLI 인터페이스 (선택적)
│           ├── __init__.py
│           └── commands.py
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── domains/               # 도메인 단위 테스트
│   │   ├── datasource/
│   │   ├── catalog/
│   │   ├── discovery/
│   │   ├── texttosql/
│   │   ├── analysis/
│   │   └── dashboard/
│   ├── integration/
│   │   ├── api/                 # API 통합 테스트
│   │   └── infrastructure/       # 인프라 통합 테스트
│   └── e2e/
│       └── scenarios/             # 시나리오 기반 E2E 테스트
│
└── migrations/                      # 데이터베이스 마이그레이션
    ├── versions/
    ├── env.py
    └── alembic.ini
```

## 도메인별 상세 구조 예시

### 1. 데이터 소스 도메인 (datasource)

#### Domain Layer
```python
# domains/datasource/domain/models.py
from sqlalchemy import Column, String, JSONB, DateTime
from app.shared.domain.base import BaseEntity

class DataSource(BaseEntity):
    __tablename__ = "data_sources"
    
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=False)  # 암호화된 설정
    status = Column(String(20), default="disconnected")
    
class ConnectionConfig:
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password  # 암호화된 비밀번호
    
    def encrypt_password(self, encryption_key: str) -> str:
        # AES-256-GCM 암호화
        pass
    
    def decrypt_password(self, encryption_key: str) -> str:
        # AES-256-GCM 복호화
        pass

# domains/datasource/domain/value_objects.py
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class DataSourceId:
    value: UUID
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("DataSourceId cannot be empty")

@dataclass
class ConnectionString:
    host: str
    port: int
    database: str
    username: str
    
    def build(self, include_password: bool = False) -> str:
        if include_password:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"
```

#### Repository Interface
```python
# domains/datasource/domain/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from .value_objects import DataSourceId

class DataSourceRepositoryInterface(ABC):
    @abstractmethod
    async def save(self, datasource) -> DataSource:
        pass
    
    @abstractmethod
    async def find_by_id(self, id: DataSourceId) -> Optional[DataSource]:
        pass
    
    @abstractmethod
    async def find_all(self) -> List[DataSource]:
        pass
    
    @abstractmethod
    async def delete(self, id: DataSourceId) -> bool:
        pass
```

#### Application Service
```python
# domains/datasource/application/services.py
from typing import List, Optional
from ..domain.repositories import DataSourceRepositoryInterface
from ..domain.models import DataSource
from ..domain.value_objects import DataSourceId, ConnectionConfig
from .dto import CreateDataSourceRequest, DataSourceResponse

class DataSourceApplicationService:
    def __init__(self, repository: DataSourceRepositoryInterface):
        self.repository = repository
    
    async def create_datasource(self, request: CreateDataSourceRequest) -> DataSourceResponse:
        # 비즈니스 로직 검증
        connection_config = ConnectionConfig(
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password
        )
        
        # 연결 테스트
        if not await self._test_connection(connection_config):
            raise ValueError("Connection test failed")
        
        # 데이터 소스 생성
        datasource = DataSource(
            name=request.name,
            type=request.type,
            config=connection_config.to_encrypted_json()
        )
        
        saved_datasource = await self.repository.save(datasource)
        return DataSourceResponse.from_entity(saved_datasource)
    
    async def _test_connection(self, config: ConnectionConfig) -> bool:
        # 실제 연결 테스트 로직
        pass
```

### 2. 카탈로그 도메인 (catalog)

#### Domain Models
```python
# domains/catalog/domain/models.py
from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from app.shared.domain.base import BaseEntity

class Schema(BaseEntity):
    __tablename__ = "schemas"
    
    data_source_id = Column(String, ForeignKey("data_sources.id"), nullable=False)
    schema_name = Column(String(255), nullable=False)
    
    tables = relationship("Table", back_populates="schema")

class Table(BaseEntity):
    __tablename__ = "tables"
    
    schema_id = Column(String, ForeignKey("schemas.id"), nullable=False)
    table_name = Column(String(255), nullable=False)
    table_type = Column(String(20), default="table")
    row_count = Column(Integer, default=0)
    description = Column(Text)
    tags = Column(ARRAY(String))
    
    schema = relationship("Schema", back_populates="tables")
    columns = relationship("Column", back_populates="table")

class Column(BaseEntity):
    __tablename__ = "columns"
    
    table_id = Column(String, ForeignKey("tables.id"), nullable=False)
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    
    table = relationship("Table", back_populates="columns")
```

### 3. 발견 도메인 (discovery)

#### Domain Services
```python
# domains/discovery/domain/services.py
from typing import List
from ..domain.models import Document, EmbeddingVector
from ..domain.value_objects import SearchQuery, SearchResult

class VectorSearchService:
    def __init__(self, embedding_generator, vector_repository):
        self.embedding_generator = embedding_generator
        self.vector_repository = vector_repository
    
    async def search_similar_documents(self, query: SearchQuery) -> List[SearchResult]:
        # 쿼리 임베딩 생성
        query_embedding = await self.embedding_generator.generate(query.text)
        
        # 벡터 유사도 검색
        similar_documents = await self.vector_repository.find_similar(
            query_embedding, 
            limit=query.limit,
            threshold=query.similarity_threshold
        )
        
        return [
            SearchResult(
                document=doc,
                relevance_score=doc.calculate_similarity(query_embedding),
                snippet=doc.generate_snippet(query.text)
            )
            for doc in similar_documents
        ]
    
    async def index_document(self, document: Document) -> None:
        # 문서 임베딩 생성 및 저장
        embedding = await self.embedding_generator.generate(document.content)
        vector = EmbeddingVector(
            document_id=document.id,
            vector=embedding,
            metadata=document.get_metadata()
        )
        await self.vector_repository.save(vector)
```

## 도메인 분리의 장점

### 1. 명확한 경계
- **도메인 로직**: 비즈니스 규칙과 도메인 모델
- **애플리케이션 로직**: 유스케이스 조정과 외부 연동
- **인프라스트럭처**: 기술적 구현과 외부 서비스 연동

### 2. 의존성 방향
```
API Layer → Application Service → Domain Service → Repository → Infrastructure
```

### 3. 테스트 용이성
- **도메인 단위 테스트**: 비즈니스 로직 단위 테스트
- **애플리케이션 테스트**: 유스케이스 통합 테스트
- **인프라 테스트**: 외부 연동 테스트

### 4. 확장성
- **새로운 도메인 추가**: 기존 코드 영향 최소화
- **도메인 내부 변경**: 다른 도메인 영향 최소화
- **기술 스택 변경**: 도메인 로직은 기술 독립적

## 레이어별 책임

### 1. Domain Layer
- **엔티티 정의**: 비즈니스 객체와 규칙
- **값 객체**: 도메인 특정 타입 (ID, ValueObject)
- **도메인 서비스**: 복잡한 비즈니스 로직
- **리포지토리 인터페이스**: 데이터 접근 추상화

### 2. Application Layer
- **유스케이스**: 사용자 시나리오 구현
- **애플리케이션 서비스**: 도메인 조정과 외부 연동
- **DTO**: 외부 인터페이스용 데이터 전송 객체
- **의존성 주입**: 레이어 간 연결

### 3. Infrastructure Layer
- **리포지토리 구현**: 실제 데이터 접근 로직
- **외부 서비스 연동**: LLM, 데이터베이스, 스토리지
- **기술적 구현**: 보안, 로깅, 모니터링

### 4. Interface Layer
- **API 라우터**: HTTP 엔드포인트 정의
- **요청/응답 변환**: DTO ↔ 엔티티 변환
- **인증/인가**: 보안 관련 처리
- **미들웨어**: 공통 처리 로직

## 실제 적용 가이드

### 1. 단계적 마이그레이션
1. **1단계**: 도메인별 폴더 구조 생성
2. **2단계**: 도메인 모델 이전 및 리팩토링
3. **3단계**: 애플리케이션 서비스 분리
4. **4단계**: 인프라스트럭처 계층 정리
5. **5단계**: API 레이어 재구성

### 2. 팀 협업 방식
- **도메인별 팀 구성**: 각 도메인 전담 팀
- **코드 리뷰**: 도메인 경계 준수 검토
- **통합 테스트**: 도메인 간 연동 검증
- **지식 공유**: 도메인별 비즈니스 로직 문서화

이 구조를 통해 장기적으로 유지보수가 쉽고, 확장성이 뛰어난 시스템을 구축할 수 있습니다.
