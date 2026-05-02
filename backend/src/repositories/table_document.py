from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import TableDocument


class TableDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def semantic_search(
        self,
        embedding: list[float],
        *,
        schema_name: Optional[str] = None,
        table_only: bool = False,
        column_only: bool = False,
        limit: int = 10,
        min_similarity: float = 0.3,
    ) -> list[tuple[TableDocument, float]]:
        max_distance = 1.0 - min_similarity
        similarity_expr = (1 - TableDocument.embedding.cosine_distance(embedding)).label("similarity")
        stmt = (
            select(TableDocument, similarity_expr)
            .where(TableDocument.embedding.isnot(None))
            .where(TableDocument.embedding.cosine_distance(embedding) < max_distance)
        )
        if schema_name:
            stmt = stmt.where(TableDocument.schema_name == schema_name)
        if table_only:
            stmt = stmt.where(TableDocument.column_name.is_(None))
        elif column_only:
            stmt = stmt.where(TableDocument.column_name.isnot(None))
        stmt = stmt.order_by(TableDocument.embedding.cosine_distance(embedding)).limit(limit)
        result = await self._session.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]

    async def find_by_table_id(self, table_id: UUID) -> list[TableDocument]:
        result = await self._session.execute(
            select(TableDocument).where(TableDocument.table_id == table_id)
        )
        return list(result.scalars().all())

    async def delete_by_schema_names(self, schema_names: list[str]) -> None:
        if not schema_names:
            return
        await self._session.execute(
            delete(TableDocument).where(TableDocument.schema_name.in_(schema_names))
        )

    async def update_content_and_embedding(
        self,
        table_id: UUID,
        column_name: Optional[str],
        content: str,
        embedding: list[float],
    ) -> None:
        result = await self._session.execute(
            select(TableDocument).where(
                TableDocument.table_id == table_id,
                TableDocument.column_name == column_name,
            )
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            return
        doc.content = content
        doc.embedding = embedding
        await self._session.flush()

    async def create_bulk(self, docs: list[TableDocument]) -> None:
        for doc in docs:
            self._session.add(doc)
        await self._session.flush()
