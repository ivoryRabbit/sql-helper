import logging
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Optional
from uuid import UUID

import sqlparse
from fastapi import HTTPException

from clients.embedding import EmbeddingClient
from clients.llm import LLMClient, LLMMessage
from models.entities import ConversationMessage, ConversationSession, SqlGeneration, TableDocument
from models.request.sql_assistant import (
    CreateSessionRequest,
    ExplainRequest,
    GenerateRequest,
    OptimizeRequest,
    ValidateRequest,
)
from models.response.sql_assistant import (
    ErrorEvent,
    ExplainResponse,
    GenerationCompleteEvent,
    MessageResponse,
    OptimizeResponse,
    SessionDetailResponse,
    SessionResponse,
    SqlChunkEvent,
    SqlGenerationHistoryItem,
    ValidationResponse,
    ValidationResult,
)
from repositories.sql_assistant import (
    ConversationMessageRepository,
    ConversationSessionRepository,
    SqlGenerationRepository,
)
from repositories.table_document import TableDocumentRepository

logger = logging.getLogger(__name__)

_PROMPT_CACHE: dict[str, str] = {}
# backend/src/services/ → backend/src/ → backend/src/agents/docs/
_AGENTS_DOCS_DIR = Path(__file__).parent.parent / "agents" / "docs"

_DANGEROUS_PATTERN = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|UPDATE|INSERT|GRANT|REVOKE|ALTER|CREATE|REPLACE)\b",
    re.IGNORECASE,
)


class SqlAssistantService:
    def __init__(
        self,
        generation_repo: SqlGenerationRepository,
        session_repo: ConversationSessionRepository,
        message_repo: ConversationMessageRepository,
        doc_repo: TableDocumentRepository,
        embedding_client: EmbeddingClient,
        llm_client: LLMClient,
    ) -> None:
        self._generation_repo = generation_repo
        self._session_repo = session_repo
        self._message_repo = message_repo
        self._doc_repo = doc_repo
        self._embedding_client = embedding_client
        self._llm_client = llm_client

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_sql_streaming(
        self, request: GenerateRequest
    ) -> AsyncIterator[dict]:
        dialect = request.options.sql_dialect

        if request.session_id is not None:
            session = await self._session_repo.get(request.session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")

        logger.info(
            "SQL generation started: query=%r dialect=%s data_source_id=%s session_id=%s",
            request.query, dialect, request.data_source_id, request.session_id,
        )

        embedding = await self._embedding_client.embed(request.query)
        docs = await self._doc_repo.semantic_search(embedding, limit=5)
        logger.debug("Retrieved %d context docs for query", len(docs))
        schema_context = self._build_schema_context(docs)
        messages = await self._build_messages(
            request.query, schema_context, dialect, request.session_id
        )

        generation = await self._generation_repo.create(
            session_id=request.session_id,
            user_query=request.query,
            data_source_id=request.data_source_id,
            selected_tables=request.selected_tables,
            llm_model=self._llm_client._model,
            validation_status="pending",
        )

        full_response = ""
        try:
            async for chunk in self._llm_client.stream_generate(messages):
                full_response += chunk
                event = SqlChunkEvent(
                    content=chunk,
                    generation_id=generation.id,
                )
                yield event.model_dump()

            sql = self._extract_sql(full_response)
            validation = self._validate_syntax(sql)
            explanation = (
                self._extract_explanation(full_response, sql)
                if request.options.include_explanation
                else None
            )

            await self._generation_repo.update(
                generation.id,
                generated_sql=sql,
                explanation=explanation,
                validation_status="valid" if validation.is_valid else "invalid",
                validation_errors=validation.syntax_errors + validation.security_issues or None,
                llm_tokens_used=None,
            )

            if request.session_id is not None:
                await self._message_repo.create(
                    session_id=request.session_id,
                    role="user",
                    content=request.query,
                )
                await self._message_repo.create(
                    session_id=request.session_id,
                    role="assistant",
                    content=full_response,
                    sql_generation_id=generation.id,
                )
                await self._session_repo.update(request.session_id)

            logger.info(
                "SQL generation complete: generation_id=%s valid=%s sql_len=%d",
                generation.id, validation.is_valid, len(sql),
            )
            complete_event = GenerationCompleteEvent(
                generation_id=generation.id,
                sql=sql,
                explanation=explanation,
                confidence_score=None,
                validation=validation,
            )
            yield complete_event.model_dump()

        except Exception as exc:
            logger.error(
                "SQL generation failed: generation_id=%s error=%s",
                generation.id, exc, exc_info=True,
            )
            await self._generation_repo.update(
                generation.id, validation_status="invalid"
            )
            error_event = ErrorEvent(
                message=str(exc),
                generation_id=generation.id,
            )
            yield error_event.model_dump()

    async def validate_sql(self, request: ValidateRequest) -> ValidationResponse:
        validation = self._validate_syntax(request.sql)
        return ValidationResponse(sql=request.sql, validation=validation)

    async def explain_sql(self, request: ExplainRequest) -> ExplainResponse:
        system_prompt = self._load_system_prompt(request.dialect)
        messages: list[LLMMessage] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Explain what the following SQL query does in plain English:\n\n"
                    f"```sql\n{request.sql}\n```"
                ),
            },
        ]
        explanation, _ = await self._llm_client.generate(messages)
        return ExplainResponse(sql=request.sql, explanation=explanation)

    async def optimize_sql(self, request: OptimizeRequest) -> OptimizeResponse:
        system_prompt = self._load_system_prompt(request.dialect)
        messages: list[LLMMessage] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Review the following SQL query and suggest optimizations. "
                    f"List each suggestion on a new line. "
                    f"If you can produce an optimized version, provide it in a ```sql code fence.\n\n"
                    f"```sql\n{request.sql}\n```"
                ),
            },
        ]
        response, _ = await self._llm_client.generate(messages)
        optimized_sql = self._extract_sql(response) if "```sql" in response else None
        suggestions = [
            line.strip("- ").strip()
            for line in response.splitlines()
            if line.strip() and not line.strip().startswith("```")
        ]
        return OptimizeResponse(
            sql=request.sql,
            suggestions=suggestions,
            optimized_sql=optimized_sql,
        )

    async def get_history(self, limit: int = 50) -> list[SqlGenerationHistoryItem]:
        rows = await self._generation_repo.list_recent(limit)
        return [SqlGenerationHistoryItem.model_validate(row) for row in rows]

    async def create_session(self, request: CreateSessionRequest) -> SessionResponse:
        session = await self._session_repo.create(
            title=request.title,
            data_source_id=request.data_source_id,
        )
        return SessionResponse.model_validate(session)

    async def list_sessions(self) -> list[SessionResponse]:
        sessions = await self._session_repo.list_all()
        return [SessionResponse.model_validate(s) for s in sessions]

    async def get_session(self, session_id: UUID) -> SessionDetailResponse:
        session = await self._session_repo.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        messages = await self._message_repo.get_by_session(session_id)
        return SessionDetailResponse(
            session=SessionResponse.model_validate(session),
            messages=[MessageResponse.model_validate(m) for m in messages],
        )

    async def delete_session(self, session_id: UUID) -> None:
        session = await self._session_repo.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        await self._message_repo.delete_by_session(session_id)
        await self._session_repo.delete(session_id)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _load_system_prompt(dialect: str) -> str:
        if dialect not in _PROMPT_CACHE:
            prompt_path = _AGENTS_DOCS_DIR / f"{dialect}.md"
            _PROMPT_CACHE[dialect] = prompt_path.read_text(encoding="utf-8")
        return _PROMPT_CACHE[dialect]

    @staticmethod
    def _build_schema_context(
        docs: list[tuple[TableDocument, float]],
    ) -> str:
        grouped: dict[str, list[str]] = {}
        for doc, _ in docs:
            key = f"{doc.schema_name}.{doc.table_name}"
            grouped.setdefault(key, []).append(doc.content)

        parts: list[str] = []
        for table_key, contents in grouped.items():
            parts.append(f"Table: {table_key}")
            for content in contents:
                parts.append(content)
            parts.append("")
        return "\n".join(parts)

    async def _build_messages(
        self,
        user_query: str,
        schema_context: str,
        dialect: str,
        session_id: Optional[UUID],
    ) -> list[LLMMessage]:
        system_prompt = self._load_system_prompt(dialect)
        if schema_context:
            system_prompt += f"\n\n## Available Tables\n\n{schema_context}"

        messages: list[LLMMessage] = [{"role": "system", "content": system_prompt}]

        if session_id is not None:
            history = await self._message_repo.get_by_session(session_id, limit=10)
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": user_query})
        return messages

    @staticmethod
    def _extract_sql(llm_response: str) -> str:
        # CTE pattern
        sqls = re.findall(r"WITH.*?;", llm_response, re.DOTALL | re.IGNORECASE)
        if sqls:
            return sqls[-1]
        # SELECT pattern
        sqls = re.findall(r"SELECT.*?;", llm_response, re.DOTALL | re.IGNORECASE)
        if sqls:
            return sqls[-1]
        # Markdown ```sql fence
        sqls = re.findall(r"```sql\n(.*?)```", llm_response, re.DOTALL)
        if sqls:
            return sqls[-1].strip()
        # Generic markdown fence
        sqls = re.findall(r"```(.*?)```", llm_response, re.DOTALL)
        if sqls:
            return sqls[-1].strip()
        return llm_response

    @staticmethod
    def _extract_explanation(full_response: str, sql: str) -> Optional[str]:
        explanation = full_response.replace(sql, "").strip()
        explanation = re.sub(r"```sql.*?```", "", explanation, flags=re.DOTALL).strip()
        explanation = re.sub(r"```.*?```", "", explanation, flags=re.DOTALL).strip()
        return explanation if explanation else None

    @staticmethod
    def _validate_syntax(sql: str) -> ValidationResult:
        errors: list[str] = []
        security: list[str] = []

        if not sql.strip():
            errors.append("Empty SQL statement")
            return ValidationResult(is_valid=False, syntax_errors=errors)

        parsed = sqlparse.parse(sql.strip())
        if not parsed:
            errors.append("Could not parse SQL statement")
            return ValidationResult(is_valid=False, syntax_errors=errors)

        stmt_type = parsed[0].get_type()
        if stmt_type != "SELECT":
            errors.append(
                f"Only SELECT statements are allowed (got: {stmt_type or 'UNKNOWN'})"
            )

        match = _DANGEROUS_PATTERN.search(sql)
        if match:
            security.append(f"Dangerous keyword detected: {match.group().upper()}")

        return ValidationResult(
            is_valid=len(errors) == 0 and len(security) == 0,
            syntax_errors=errors,
            security_issues=security,
        )
