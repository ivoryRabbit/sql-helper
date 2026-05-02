---
name: py-test
description: Set up and write Python FastAPI integration/unit tests. Use when asked to "테스트 작성", "테스트 환경 구축", "add tests", "write tests", "테스트 코드", or invokes /py-test.
---

# Python FastAPI 테스트 패턴

`pytest` + `pytest-asyncio` + `httpx`를 사용한 FastAPI 통합/단위 테스트 패턴.  
이 스킬은 이 프로젝트에서 직접 구축·검증한 베스트 프랙티스다.

---

## 스택 한 줄 요약

| 역할 | 도구 | TypeScript 대응 |
|---|---|---|
| 테스트 러너 | `pytest` | Jest / Vitest |
| async 지원 | `pytest-asyncio` | 기본 내장 |
| HTTP 클라이언트 | `httpx.AsyncClient` | supertest |
| 커버리지 | `pytest-cov` | c8 / nyc |
| Fake 외부 의존성 | 직접 작성한 클래스 | jest.mock |

---

## 설치

```bash
# backend/requirements-test.txt
pytest==8.3.5
pytest-asyncio==0.24.0
pytest-cov==6.0.0

pip install -r requirements.txt -r requirements-test.txt
```

---

## pytest.ini 필수 설정

```ini
[pytest]
asyncio_mode = auto       # 모든 async def test_*를 자동으로 코루틴으로 실행
testpaths = test
pythonpath = src          # src/ 없이는 from models import ... 가 실패함

addopts = -v --tb=short
log_cli = true
log_cli_level = WARNING
```

`asyncio_mode = auto` 없으면 모든 async 테스트 함수에 `@pytest.mark.asyncio`를 일일이 붙여야 한다.

---

## 핵심 패턴 1 — Transaction Rollback으로 DB 격리

테스트마다 DB를 초기화하거나 별도 DB를 쓰지 않아도 된다.  
**트랜잭션을 열고, 테스트 후 롤백**하면 DB 상태가 원상복구된다.

```python
# test/conftest.py

@pytest_asyncio.fixture(scope="session")
async def engine():
    """한 번만 생성. 스키마와 테이블을 초기화."""
    eng = create_async_engine(settings.database_url, echo=False)
    async with eng.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS data_catalog"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        from models import entities  # noqa — ORM 메타데이터 등록
        await conn.run_sync(ModelBase.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_connection(engine):
    """테스트마다 트랜잭션 시작 → 테스트 후 롤백."""
    async with engine.connect() as conn:
        await conn.begin()
        yield conn
        await conn.rollback()   # ← 여기서 테스트 중 쓴 데이터 전부 사라짐


@pytest_asyncio.fixture
async def db_session(db_connection):
    """
    join_transaction_mode="create_savepoint":
    서비스/레포 내부의 session.commit()이 SAVEPOINT만 생성하고
    outer 트랜잭션은 커밋되지 않는다.
    """
    session = AsyncSession(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    yield session
    await session.close()
```

### 왜 `expire_on_commit=False`?

`session.commit()` 후 SQLAlchemy가 기본적으로 객체를 "expired" 상태로 만든다.  
다음 접근 시 SELECT를 다시 날리는데, 테스트 트랜잭션이 롤백 중이면 오류가 난다.  
`expire_on_commit=False`로 커밋 후에도 객체를 메모리에서 읽을 수 있게 한다.

---

## 핵심 패턴 2 — FastAPI HTTP 테스트

```python
@pytest_asyncio.fixture
async def client(db_session):
    from main import create_app
    from dependencies import get_session

    app = create_app()

    # lifespan 교체: Temporal / MinIO 연결 건너뜀
    @asynccontextmanager
    async def test_lifespan(app):
        db = container.database_manager()
        await db.initialize()
        yield
        await db.close()

    app.router.lifespan_context = test_lifespan

    # get_session을 테스트 트랜잭션 세션으로 교체
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    app.dependency_overrides.clear()
```

### 테스트에서 사용

```python
async def test_creates_source(client: AsyncClient):
    resp = await client.post("/api/v1/data-sources", json={...})
    assert resp.status_code == 201
```

TypeScript의 `await request(app).post('/api/data-sources').send({...}).expect(201)` 과 동일.

---

## 핵심 패턴 3 — Fake 외부 의존성

LLM, 외부 API 등은 실제 호출하지 않고 Fake 클래스로 교체한다.  
인터페이스(메서드 시그니처)만 맞추면 된다 — Python은 duck typing.

```python
# test/fakes/llm.py

class FakeLLMClient:
    def __init__(self):
        self.next_response = "SELECT 1"
        self.next_tokens = 10
        self.stream_chunks = ["SELECT 1"]
        self.generate_calls = []   # 어떤 메시지가 왔는지 검증용

    async def generate(self, messages, temperature=0.1):
        self.generate_calls.append(messages)
        return self.next_response, self.next_tokens

    async def stream_generate(self, messages, temperature=0.1):
        self.stream_calls.append(messages)
        for chunk in self.stream_chunks:
            yield chunk
```

### dependency-injector 컨테이너에 주입

```python
@pytest.fixture
def fake_llm():
    from test.fakes.llm import FakeLLMClient
    fake = FakeLLMClient()
    container.llm_client.override(fake)
    yield fake
    container.llm_client.reset_override()   # 반드시 복원

# 테스트에서:
async def test_generates_sql(client, fake_llm):
    fake_llm.next_response = "SELECT id FROM users"
    resp = await client.post("/api/v1/text-to-sql/generate", json={...})
    assert "SELECT" in resp.text
    assert len(fake_llm.generate_calls) == 1  # 실제로 호출됐는지 확인
```

---

## 단위 테스트 vs 통합 테스트

```
        ▲  E2E 테스트         (브라우저 자동화 — 이 프로젝트에선 생략)
       ▲▲▲  통합 테스트        ← client 픽스처 사용, 실제 DB 히트
      ▲▲▲▲▲  단위 테스트       ← DB 없이 서비스 로직만 테스트
```

### 단위 테스트 예시 (DB 없음)

```python
async def test_encrypt_password_before_save():
    fake_repo = AsyncMock()
    fake_repo.get_by_name.return_value = None
    fake_repo.create.return_value = DataSource(id=uuid4(), name="x", config={"password": "enc"}, ...)

    service = DataSourceService(repository=fake_repo, encryption=EncryptionService(key=TEST_KEY))
    await service.create(DataSourceCreate(name="x", type="postgresql", config={"password": "plaintext"}))

    saved_config = fake_repo.create.call_args.kwargs["config"]
    assert saved_config["password"] != "plaintext"   # 암호화 검증
```

### 어떤 걸 쓸지 기준

| 상황 | 추천 |
|---|---|
| 비즈니스 로직 검증 (암호화, 계산, 분기) | 단위 테스트 |
| API 계약 확인 (상태코드, 응답 shape) | 통합 테스트 |
| pgvector 코사인 검색 정확도 | 통합 테스트 (실제 DB 필수) |
| LLM 프롬프트 파이프라인 | 통합 테스트 + FakeLLM |
| Pydantic 스키마 검증 | 단위 테스트 (모델 직접 인스턴스화) |

---

## 테스트 구조 컨벤션

```
backend/test/
├── conftest.py              — engine, db_session, client, fake_llm 픽스처
├── fakes/
│   ├── __init__.py
│   └── llm.py               — FakeLLMClient
├── test_data_source.py      — 기능별 파일 분리
├── test_data_catalog.py
└── test_text_to_sql.py
```

테스트 클래스로 관련 케이스 묶기:

```python
class TestCreateDataSource:
    async def test_creates_and_returns_201(self, client): ...
    async def test_duplicate_name_returns_409(self, client): ...
    async def test_missing_field_returns_422(self, client): ...

class TestDeleteDataSource:
    async def test_delete_returns_204(self, client): ...
    async def test_unknown_id_returns_404(self, client): ...
```

---

## 유의사항 — 자주 빠지는 함정

### ❌ `asyncio_mode = auto` 누락

```python
# 이렇게 하면 테스트가 코루틴으로 실행되지 않아 항상 통과
async def test_something():
    assert False   # 통과해버림!
```

`pytest.ini`에 `asyncio_mode = auto` 반드시 설정.

---

### ❌ `scope="session"` fixture를 `scope="function"` fixture가 요청

```python
@pytest_asyncio.fixture(scope="session")
async def engine(): ...

@pytest_asyncio.fixture  # scope="function" (기본값)
async def db_session(engine): ...  # OK — 상위 스코프 요청 가능

@pytest_asyncio.fixture(scope="session")
async def some_session_fixture(db_session): ...  # ❌ 하위 스코프를 세션 fixture에서 요청 불가
```

스코프는 항상 `session → module → class → function` 방향으로만 의존해야 한다.

---

### ❌ `app.dependency_overrides` 정리 안 함

```python
app.dependency_overrides[get_session] = override
yield client
# 정리 안 하면 다음 테스트에도 override가 살아있음
app.dependency_overrides.clear()  # ← 반드시
```

---

### ❌ 트랜잭션 내에서 DDL 실행

```python
async with engine.connect() as conn:
    await conn.begin()
    await conn.execute(text("CREATE TABLE ..."))  # DDL은 암묵적 commit 발생
    yield conn
    await conn.rollback()   # 이미 커밋됐으므로 롤백 안 됨
```

테스트 격리용 트랜잭션 안에서 DDL(CREATE/DROP/ALTER)을 실행하지 않는다.  
스키마 생성은 `scope="session"` 픽스처에서만.

---

### ❌ 기존 committed 데이터를 "빈 DB"로 가정

```python
async def test_list_is_empty(client):
    resp = await client.get("/api/v1/data-sources")
    assert resp.json() == []   # ← 개발 DB에 이미 데이터가 있으면 실패
```

트랜잭션 롤백은 **이 테스트의 쓰기만** 되돌린다. 이전에 커밋된 데이터는 여전히 보인다.  
절대값 비교 대신 상대적 비교를 사용한다:

```python
async def test_created_source_appears_in_list(client):
    before = len((await client.get("/api/v1/data-sources")).json())
    await client.post("/api/v1/data-sources", json=PAYLOAD)
    after = (await client.get("/api/v1/data-sources")).json()
    assert len(after) == before + 1
```

---

### ❌ `AsyncMock` 없이 동기 Mock으로 async 메서드 교체

```python
from unittest.mock import MagicMock

repo = MagicMock()
repo.get.return_value = some_entity   # ← async def get()은 await 하므로 MagicMock이 안 됨
```

```python
from unittest.mock import AsyncMock

repo = AsyncMock()
repo.get.return_value = some_entity   # ✓ await repo.get() 정상 작동
```

---

## 실행 명령어

```bash
# 전체
cd backend && pytest

# 특정 파일
pytest test/test_data_source.py

# 특정 클래스/테스트
pytest test/test_data_source.py::TestCreateDataSource
pytest test/test_data_source.py::TestCreateDataSource::test_creates_and_returns_201

# 커버리지
pytest --cov=src --cov-report=term-missing

# 실패 시 즉시 중단
pytest -x

# 마지막 실패한 테스트만 재실행
pytest --lf
```

---

## 이 프로젝트 파일 위치

| 파일 | 역할 |
|---|---|
| [backend/pytest.ini](../../../backend/pytest.ini) | pytest 설정 |
| [backend/requirements-test.txt](../../../backend/requirements-test.txt) | 테스트 전용 의존성 |
| [backend/test/conftest.py](../../../backend/test/conftest.py) | engine / db_session / client / fake_llm 픽스처 |
| [backend/test/fakes/llm.py](../../../backend/test/fakes/llm.py) | FakeLLMClient |
| [backend/test/test_data_source.py](../../../backend/test/test_data_source.py) | 통합 테스트 예시 |
