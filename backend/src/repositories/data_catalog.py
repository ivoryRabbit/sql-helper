from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import Column, Schema, Table


class DataCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Schema ─────────────────────────────────────────────────────────────────

    async def list_schemas(self, data_source_id: Optional[UUID] = None) -> list[Schema]:
        stmt = select(Schema)
        if data_source_id:
            stmt = stmt.where(Schema.data_source_id == data_source_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_schemas_by_source(self, data_source_id: UUID) -> list[Schema]:
        result = await self._session.execute(
            select(Schema).where(Schema.data_source_id == data_source_id)
        )
        return list(result.scalars().all())

    async def upsert_schema(self, data_source_id: UUID, schema_name: str) -> Schema:
        result = await self._session.execute(
            select(Schema).where(
                Schema.data_source_id == data_source_id,
                Schema.schema_name == schema_name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        schema = Schema(data_source_id=data_source_id, schema_name=schema_name)
        self._session.add(schema)
        await self._session.flush()
        await self._session.refresh(schema)
        return schema

    async def delete_stale_schemas(
        self, data_source_id: UUID, active_schema_names: list[str]
    ) -> None:
        await self._session.execute(
            delete(Schema).where(
                Schema.data_source_id == data_source_id,
                Schema.schema_name.not_in(active_schema_names),
            )
        )

    # ── Table ──────────────────────────────────────────────────────────────────

    async def list_tables(
        self,
        data_source_id: Optional[UUID] = None,
        schema_id: Optional[UUID] = None,
        table_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[tuple[Table, str]]:
        stmt = select(Table, Schema.schema_name).join(Schema, Table.schema_id == Schema.id)
        if data_source_id:
            stmt = stmt.where(Schema.data_source_id == data_source_id)
        if schema_id:
            stmt = stmt.where(Table.schema_id == schema_id)
        if table_type:
            stmt = stmt.where(Table.table_type == table_type)
        if search:
            stmt = stmt.where(Table.table_name.ilike(f"%{search}%"))
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_tables_by_schema(self, schema_id: UUID) -> list[Table]:
        result = await self._session.execute(
            select(Table).where(Table.schema_id == schema_id)
        )
        return list(result.scalars().all())

    async def get_table_with_schema(self, table_id: UUID) -> Optional[tuple[Table, Schema]]:
        result = await self._session.execute(
            select(Table, Schema)
            .join(Schema, Table.schema_id == Schema.id)
            .where(Table.id == table_id)
        )
        row = result.one_or_none()
        return (row[0], row[1]) if row else None

    async def get_table_by_id(self, table_id: UUID) -> Optional[Table]:
        result = await self._session.execute(
            select(Table).where(Table.id == table_id)
        )
        return result.scalar_one_or_none()

    async def upsert_table(
        self,
        schema_id: UUID,
        table_name: str,
        table_type: str = "table",
        row_count: int = 0,
        source_description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Table:
        result = await self._session.execute(
            select(Table).where(
                Table.schema_id == schema_id,
                Table.table_name == table_name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.table_type = table_type
            existing.row_count = row_count
            existing.source_description = source_description
            # user_description is intentionally not touched
            await self._session.flush()
            return existing
        table = Table(
            schema_id=schema_id,
            table_name=table_name,
            table_type=table_type,
            row_count=row_count,
            source_description=source_description,
            tags=tags,
        )
        self._session.add(table)
        await self._session.flush()
        await self._session.refresh(table)
        return table

    async def update_table_user_description(
        self, table_id: UUID, description: Optional[str]
    ) -> Optional[Table]:
        result = await self._session.execute(
            select(Table).where(Table.id == table_id)
        )
        table = result.scalar_one_or_none()
        if table is None:
            return None
        table.user_description = description
        await self._session.flush()
        return table

    async def delete_stale_tables(
        self, schema_id: UUID, active_table_names: list[str]
    ) -> None:
        await self._session.execute(
            delete(Table).where(
                Table.schema_id == schema_id,
                Table.table_name.not_in(active_table_names),
            )
        )

    # ── Column ─────────────────────────────────────────────────────────────────

    async def get_columns_by_table(self, table_id: UUID) -> list[Column]:
        result = await self._session.execute(
            select(Column)
            .where(Column.table_id == table_id)
            .order_by(Column.ordinal_position)
        )
        return list(result.scalars().all())

    async def get_column_by_id(self, column_id: UUID) -> Optional[Column]:
        result = await self._session.execute(
            select(Column).where(Column.id == column_id)
        )
        return result.scalar_one_or_none()

    async def upsert_column(
        self,
        table_id: UUID,
        column_name: str,
        data_type: str,
        ordinal_position: int,
        is_nullable: bool = True,
        default_value: Optional[str] = None,
        is_primary_key: bool = False,
        is_foreign_key: bool = False,
        references_column: Optional[str] = None,
        source_description: Optional[str] = None,
    ) -> Column:
        result = await self._session.execute(
            select(Column).where(
                Column.table_id == table_id,
                Column.column_name == column_name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.data_type = data_type
            existing.ordinal_position = ordinal_position
            existing.is_nullable = is_nullable
            existing.default_value = default_value
            existing.is_primary_key = is_primary_key
            existing.is_foreign_key = is_foreign_key
            existing.references_column = references_column
            existing.source_description = source_description
            # user_description is intentionally not touched
            await self._session.flush()
            return existing
        column = Column(
            table_id=table_id,
            column_name=column_name,
            data_type=data_type,
            ordinal_position=ordinal_position,
            is_nullable=is_nullable,
            default_value=default_value,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
            references_column=references_column,
            source_description=source_description,
        )
        self._session.add(column)
        await self._session.flush()
        return column

    async def update_column_user_description(
        self, column_id: UUID, description: Optional[str]
    ) -> Optional[Column]:
        result = await self._session.execute(
            select(Column).where(Column.id == column_id)
        )
        column = result.scalar_one_or_none()
        if column is None:
            return None
        column.user_description = description
        await self._session.flush()
        return column

    async def delete_stale_columns(
        self, table_id: UUID, active_column_names: list[str]
    ) -> None:
        await self._session.execute(
            delete(Column).where(
                Column.table_id == table_id,
                Column.column_name.not_in(active_column_names),
            )
        )

    # ── Search ─────────────────────────────────────────────────────────────────

    async def search_tables(self, q: str) -> list[tuple[Table, str]]:
        result = await self._session.execute(
            select(Table, Schema.schema_name)
            .join(Schema, Table.schema_id == Schema.id)
            .where(Table.table_name.ilike(f"%{q}%"))
        )
        return [(row[0], row[1]) for row in result.all()]

    async def search_columns(self, q: str) -> list[tuple[Column, str, str]]:
        result = await self._session.execute(
            select(Column, Table.table_name, Schema.schema_name)
            .join(Table, Column.table_id == Table.id)
            .join(Schema, Table.schema_id == Schema.id)
            .where(Column.column_name.ilike(f"%{q}%"))
        )
        return [(row[0], row[1], row[2]) for row in result.all()]

    # ── Stats ──────────────────────────────────────────────────────────────────

    async def get_stats(self) -> dict:
        schemas_count = await self._session.scalar(select(func.count(Schema.id)))
        tables_count = await self._session.scalar(select(func.count(Table.id)))
        columns_count = await self._session.scalar(select(func.count(Column.id)))
        sources_count = await self._session.scalar(
            select(func.count(func.distinct(Schema.data_source_id)))
        )
        last_updated = await self._session.scalar(select(func.max(Table.updated_at)))
        return {
            "total_schemas": schemas_count or 0,
            "total_tables": tables_count or 0,
            "total_columns": columns_count or 0,
            "data_sources": sources_count or 0,
            "last_updated": last_updated,
        }
