from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import ConversationMessage, ConversationSession, SqlGeneration
from repositories.base import BaseRepository


class SqlGenerationRepository(BaseRepository[SqlGeneration]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlGeneration)

    async def list_recent(self, limit: int = 50) -> list[SqlGeneration]:
        result = await self._session.execute(
            select(SqlGeneration)
            .order_by(SqlGeneration.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ConversationSessionRepository(BaseRepository[ConversationSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ConversationSession)

    async def list_all(self) -> list[ConversationSession]:
        result = await self._session.execute(
            select(ConversationSession).order_by(ConversationSession.updated_at.desc())
        )
        return list(result.scalars().all())


class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ConversationMessage)

    async def get_by_session(
        self, session_id: UUID, limit: int = 50
    ) -> list[ConversationMessage]:
        result = await self._session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_by_session(self, session_id: UUID) -> None:
        await self._session.execute(
            delete(ConversationMessage).where(
                ConversationMessage.session_id == session_id
            )
        )
