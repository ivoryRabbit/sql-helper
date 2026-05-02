---
name: fastapi-di
description: Apply dependency injection using dependency-injector + FastAPI. Use when asked to "DI 적용", "의존성 주입 구현", "컨테이너 설정", "add DI pattern", or when wiring services/repos into a FastAPI app.
---

# FastAPI + dependency-injector DI 패턴

`dependency-injector` 라이브러리와 FastAPI의 `Depends`를 조합하는 올바른 패턴을 기술한다.  
이 스킬은 직접 적용 사례에서 도출된 베스트 프랙티스다.

---

## 핵심 원칙: 두 DI 시스템의 역할 분리

| 시스템 | 스코프 | 책임 |
|---|---|---|
| `dependency-injector` 컨테이너 | Application (Singleton/Factory) | 인프라 클라이언트, 설정, 서비스 |
| FastAPI `Depends` | Request | DB 세션, 인증 컨텍스트 등 요청별 상태 |

이 두 시스템을 **억지로 통합하려 하지 말 것**. 각자 잘하는 일이 다르다.

---

## 아키텍처 패턴

### 1. container.py — 싱글톤과 서비스 Factory만 등록

```python
from dependency_injector import containers, providers

class AppContainer(containers.DeclarativeContainer):

    # ── 인프라 싱글톤 ─────────────────────────────
    settings    = providers.Singleton(Settings)
    encryption  = providers.Singleton(EncryptionService, key=settings.provided.encryption_key)
    llm_client  = providers.Singleton(LLMClient, api_key=settings.provided.openai_api_key)
    storage     = providers.Singleton(StorageClient, ...)

    # ── 서비스 Factory ─────────────────────────────
    # 규칙: 싱글톤 의존성만 여기서 선언. 레포지토리(요청 스코프)는 호출 시 주입.
    data_source_service = providers.Factory(
        DataSourceService,
        encryption=encryption,  # 컨테이너가 자동 주입
        # repository는 선언하지 않음 — dependencies.py에서 call-time에 전달
    )

container = AppContainer()
```

**레포지토리는 컨테이너에 넣지 않는다.** 레포지토리는 `AsyncSession`에 의존하고, 세션은 요청 스코프이므로 컨테이너의 싱글톤/팩토리와 스코프가 맞지 않는다.

### 2. dependencies.py — 세션을 받아 서비스 조립

```python
from configs.container import container

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    db = container.database_manager()       # 싱글톤 직접 호출 OK
    async with db.get_session() as session:
        yield session

def get_data_source_service(
    session: AsyncSession = Depends(get_session),
) -> DataSourceService:
    # 핵심 패턴: Factory를 호출할 때 세션 기반 레포지토리를 kwarg로 전달
    return container.data_source_service(
        repository=DataSourceRepository(session),
    )
    # 결과: DataSourceService(repository=<요청 레포>, encryption=<싱글톤>)
```

`providers.Factory`는 호출 시 전달된 kwargs로 선언된 의존성을 **override**한다.  
컨테이너에 선언된 나머지 싱글톤 의존성은 자동으로 주입된다.

### 3. controller.py — 변경 없음

```python
@router.get("")
async def list_items(
    service: MyService = Depends(get_my_service),
) -> list[ItemResponse]:
    return await service.list()
```

컨트롤러는 DI 구현 방식에 무관하다. FastAPI `Depends`만 사용한다.

---

## 트러블슈팅 — 흔한 실수 3가지

### ❌ 실수 1: `Provide[...]`를 FastAPI dependency 함수 파라미터로 직접 사용

```python
# 잘못된 예 — FastAPI가 MyService를 query param으로 해석해 에러 발생
@inject
def get_service(
    svc: MyService = Provide[AppContainer.service],  # ← FastAPIError!
) -> MyService:
    return svc
```

FastAPI는 dependency 함수의 파라미터를 검사해서 `FieldInfo`/`Depends` 이외의 복합 타입 기본값을 query param으로 처리하려다 실패한다.

```
fastapi.exceptions.FastAPIError: Invalid args for response field!
Hint: check that <class 'MyService'> is a valid Pydantic field type.
```

**해결**: `Provide[...]`는 엔드포인트 함수에서만 `Depends(Provide[...])` 형태로 사용하거나, 세션이 필요 없는 순수 싱글톤 서비스에 한해 사용한다.

---

### ❌ 실수 2: `session.override()`를 동시 요청에 사용

```python
# 위험! 비동기 동시 요청 간 race condition 발생
with container.session.override(providers.Object(session)):
    svc = container.my_service()  # session_A 요청이 session_B를 덮어쓸 수 있음
```

실제 테스트 결과:

```
req='session_A', got='session_C', match=False   # ← 다른 요청의 세션이 섞임
req='session_B', got='session_B', match=True
req='session_C', got='session_A', match=False
```

`container.session.override()`는 전역 상태를 수정하므로 동시 요청 환경에서 절대 사용하지 않는다.

**해결**: call-time kwargs 패턴 사용 (위 2번 패턴 참조).

---

### ❌ 실수 3: 컨테이너에 `providers.Dependency()`로 세션 슬롯을 선언한 뒤 연쇄 Factory 구성

```python
# 선언은 되지만 사용 시 문제 발생
class AppContainer(containers.DeclarativeContainer):
    session      = providers.Dependency()
    data_repo    = providers.Factory(DataRepository, session=session)
    data_service = providers.Factory(DataService, repo=data_repo)

# 이렇게 호출하면...
container.data_service(session='my_session')
# Error: Dependency "AppContainer.session" is not defined
# — 중첩 Factory에는 외부 kwargs가 전파되지 않는다.
```

`providers.Dependency()`로 선언한 슬롯은 `container.session.override()`로만 채울 수 있는데, 이건 위 실수 2의 문제가 있다.

**해결**: 연쇄 Factory 대신, 최상위 서비스 Factory에서 레포지토리를 선언 없이 call-time으로 전달한다.

```python
# 올바른 패턴
data_service = providers.Factory(DataService, encryption=encryption)
# repo는 Dependency()로 선언하지 않음

# 호출 시:
container.data_service(repo=DataRepository(session))  # kwargs override로 전달
```

---

## `providers.Factory` call-time override 동작 원리

```python
class AppContainer(containers.DeclarativeContainer):
    val     = providers.Object(42)
    service = providers.Factory(Service, val=val)  # encryption 등 싱글톤만 선언

svc = container.service(repo=SomeRepo(session))
# 내부적으로: Service(val=42, repo=SomeRepo(session))
# - val: 컨테이너가 providers.Object(42)로 resolve
# - repo: 호출 시 전달된 kwarg가 그대로 사용됨
```

**싱글톤 확인**: 같은 컨테이너에서 같은 `Singleton` 프로바이더를 여러 번 호출하면 항상 동일한 인스턴스가 반환된다.

```python
enc1 = container.encryption()
enc2 = container.encryption()
assert enc1 is enc2  # ✓ 동일 인스턴스
```

---

## 새 서비스 추가 체크리스트

1. **서비스 클래스 작성** (`services/<name>.py`): `__init__`에서 레포지토리와 싱글톤 클라이언트를 파라미터로 받는다.

2. **container.py에 Factory 등록**: 싱글톤 의존성만 선언한다.
   ```python
   my_service = providers.Factory(
       MyService,
       encryption=encryption,   # 싱글톤 → 컨테이너
       llm_client=llm_client,   # 싱글톤 → 컨테이너
       # repo는 선언하지 않음
   )
   ```

3. **dependencies.py에 팩토리 함수 추가**: 세션 기반 레포를 call-time에 전달한다.
   ```python
   def get_my_service(
       session: AsyncSession = Depends(get_session),
   ) -> MyService:
       return container.my_service(
           repo=MyRepository(session),
       )
   ```

4. **컨트롤러에서 사용**: `Depends(get_my_service)`.

---

## settings.provided 패턴

설정 값을 싱글톤 생성자에 전달할 때는 `settings.provided.<attr>` 를 사용한다.  
`settings.provided`는 프로바이더가 resolve될 때 해당 속성을 자동 추출한다.

```python
settings  = providers.Singleton(Settings)
llm_client = providers.Singleton(LLMClient, api_key=settings.provided.openai_api_key)
# 내부: LLMClient(api_key=Settings().openai_api_key)
```

`settings()` 처럼 직접 호출하거나 `settings.provided.attr` 체이닝 없이 `settings.openai_api_key` 같은 형태는 동작하지 않는다.

---

## 이 프로젝트 파일 위치 참고

| 파일 | 역할 |
|---|---|
| [backend/src/configs/container.py](../../../backend/src/configs/container.py) | AppContainer 정의 |
| [backend/src/dependencies.py](../../../backend/src/dependencies.py) | FastAPI Depends 팩토리 함수 |
| [backend/src/controllers/](../../../backend/src/controllers/) | 컨트롤러 (Depends 사용) |
