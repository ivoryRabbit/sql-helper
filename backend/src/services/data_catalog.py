import logging
from typing import Optional
from uuid import UUID

import psycopg
from fastapi import HTTPException

from clients.embedding import EmbeddingClient
from models.entities import Column, Schema, Table, TableDocument
from models.request.data_catalog import CatalogRefreshRequest, SemanticSearchRequest, SimilarTableRequest
from models.response.data_catalog import (
    CatalogRefreshResponse,
    CatalogSourceResponse,
    CatalogStatsResponse,
    ColumnResponse,
    ColumnSearchResult,
    RecommendationResponse,
    RecommendedTable,
    SchemaResponse,
    SearchHistoryItem,
    SearchResponse,
    SemanticSearchResponse,
    SemanticSearchResultItem,
    TableDetailResponse,
    TableResponse,
)
from repositories.data_catalog import DataCatalogRepository
from repositories.data_source import DataSourceRepository
from repositories.search_history import SearchHistoryRepository
from repositories.table_document import TableDocumentRepository
from utils.crypto import EncryptionService

logger = logging.getLogger(__name__)


class DataCatalogService:
    def __init__(
        self,
        repo: DataCatalogRepository,
        data_source_repo: DataSourceRepository,
        encryption: EncryptionService,
        embedding_client: Optional[EmbeddingClient] = None,
        doc_repo: Optional[TableDocumentRepository] = None,
        history_repo: Optional[SearchHistoryRepository] = None,
    ) -> None:
        self._repo = repo
        self._ds_repo = data_source_repo
        self._encryption = encryption
        self._embedding_client = embedding_client
        self._doc_repo = doc_repo
        self._history_repo = history_repo

    async def get_by_source(self, data_source_id: UUID) -> CatalogSourceResponse:
        schemas = await self._repo.get_schemas_by_source(data_source_id)
        schema_responses = []
        all_tables: list[TableResponse] = []

        for schema in schemas:
            tables = await self._repo.get_tables_by_schema(schema.id)
            table_responses = [self._table_to_response(t, schema.schema_name) for t in tables]
            all_tables.extend(table_responses)
            schema_responses.append(
                SchemaResponse(
                    id=schema.id,
                    data_source_id=schema.data_source_id,
                    schema_name=schema.schema_name,
                    table_count=len(tables),
                    created_at=schema.created_at,
                )
            )

        return CatalogSourceResponse(
            data_source_id=data_source_id,
            schemas=schema_responses,
            tables=all_tables,
        )

    async def list_tables(
        self,
        data_source_id: Optional[UUID] = None,
        schema_id: Optional[UUID] = None,
        table_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[TableResponse]:
        rows = await self._repo.list_tables(data_source_id, schema_id, table_type, search)
        return [self._table_to_response(table, schema_name) for table, schema_name in rows]

    async def get_table(self, table_id: UUID) -> TableDetailResponse:
        row = await self._repo.get_table_with_schema(table_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Table not found.")
        table, schema = row
        columns = await self._repo.get_columns_by_table(table_id)
        return TableDetailResponse(
            **self._table_to_response(table, schema.schema_name).model_dump(),
            columns=[self._column_to_response(c) for c in columns],
        )

    async def list_schemas(self, data_source_id: Optional[UUID] = None) -> list[SchemaResponse]:
        schemas = await self._repo.list_schemas(data_source_id)
        result = []
        for schema in schemas:
            tables = await self._repo.get_tables_by_schema(schema.id)
            result.append(
                SchemaResponse(
                    id=schema.id,
                    data_source_id=schema.data_source_id,
                    schema_name=schema.schema_name,
                    table_count=len(tables),
                    created_at=schema.created_at,
                )
            )
        return result

    async def search(self, q: str, search_type: Optional[str] = None) -> SearchResponse:
        tables: list[TableResponse] = []
        columns: list[ColumnSearchResult] = []

        if search_type in (None, "table"):
            rows = await self._repo.search_tables(q)
            tables = [self._table_to_response(t, sn) for t, sn in rows]

        if search_type in (None, "column"):
            rows = await self._repo.search_columns(q)
            columns = [
                ColumnSearchResult(
                    column=self._column_to_response(col),
                    table_name=tn,
                    schema_name=sn,
                )
                for col, tn, sn in rows
            ]

        return SearchResponse(tables=tables, columns=columns)

    async def refresh(self, request: CatalogRefreshRequest) -> CatalogRefreshResponse:
        data_source = await self._ds_repo.get(request.data_source_id)
        if data_source is None:
            raise HTTPException(status_code=404, detail="Data source not found.")

        config = dict(data_source.config)
        if "password" in config:
            try:
                config["password"] = self._encryption.decrypt(config["password"])
            except Exception:
                pass

        if data_source.type == "postgresql":
            return await self._refresh_postgres(data_source.id, config)

        raise HTTPException(
            status_code=422,
            detail=f"Catalog refresh not yet supported for type '{data_source.type}'.",
        )

    async def update_table_description(
        self, table_id: UUID, description: Optional[str]
    ) -> TableResponse:
        table = await self._repo.update_table_user_description(table_id, description)
        if table is None:
            raise HTTPException(status_code=404, detail="Table not found.")

        if self._embedding_client and self._doc_repo:
            try:
                columns = await self._repo.get_columns_by_table(table_id)
                row = await self._repo.get_table_with_schema(table_id)
                schema_name = row[1].schema_name if row else ""
                content = self._build_table_content(schema_name, table, columns)
                embedding = await self._embedding_client.embed(content)
                await self._doc_repo.update_content_and_embedding(
                    table_id=table_id,
                    column_name=None,
                    content=content,
                    embedding=embedding,
                )
            except Exception:
                logger.warning("Re-embedding failed after table description update", exc_info=True)

        row = await self._repo.get_table_with_schema(table_id)
        return self._table_to_response(row[0], row[1].schema_name)

    async def update_column_description(
        self, column_id: UUID, description: Optional[str]
    ) -> ColumnResponse:
        column = await self._repo.update_column_user_description(column_id, description)
        if column is None:
            raise HTTPException(status_code=404, detail="Column not found.")

        if self._embedding_client and self._doc_repo:
            try:
                table = await self._repo.get_table_by_id(column.table_id)
                if table:
                    row = await self._repo.get_table_with_schema(table.id)
                    schema_name = row[1].schema_name if row else ""
                    content = self._build_column_content(schema_name, table, column)
                    embedding = await self._embedding_client.embed(content)
                    await self._doc_repo.update_content_and_embedding(
                        table_id=table.id,
                        column_name=column.column_name,
                        content=content,
                        embedding=embedding,
                    )
            except Exception:
                logger.warning("Re-embedding failed after column description update", exc_info=True)

        return self._column_to_response(column)

    async def get_stats(self) -> CatalogStatsResponse:
        stats = await self._repo.get_stats()
        return CatalogStatsResponse(**stats)

    # ── Introspection helpers ──────────────────────────────────────────────────

    async def _refresh_postgres(
        self, data_source_id: UUID, config: dict
    ) -> CatalogRefreshResponse:
        metadata = await self._introspect_postgres(config)

        # Table documents are derived data — safe to delete and rebuild.
        # They are keyed by schema_name (not FK), so delete before schema upserts.
        if self._doc_repo:
            existing = await self._repo.get_schemas_by_source(data_source_id)
            if existing:
                await self._doc_repo.delete_by_schema_names(
                    [s.schema_name for s in existing]
                )

        schemas_synced = tables_synced = columns_synced = 0
        tables_for_indexing: list[tuple[str, Table, list[Column]]] = []
        active_schema_names = [sm["name"] for sm in metadata]

        for schema_meta in metadata:
            schema = await self._repo.upsert_schema(data_source_id, schema_meta["name"])
            schemas_synced += 1

            active_table_names = [tm["name"] for tm in schema_meta["tables"]]

            for table_meta in schema_meta["tables"]:
                table = await self._repo.upsert_table(
                    schema_id=schema.id,
                    table_name=table_meta["name"],
                    table_type=table_meta["type"],
                    row_count=table_meta["row_count"],
                    source_description=table_meta.get("source_description"),
                )
                tables_synced += 1

                active_column_names = [cm["column_name"] for cm in table_meta["columns"]]
                cols: list[Column] = []

                for col_meta in table_meta["columns"]:
                    col = await self._repo.upsert_column(table_id=table.id, **col_meta)
                    columns_synced += 1
                    cols.append(col)

                await self._repo.delete_stale_columns(table.id, active_column_names)
                tables_for_indexing.append((schema_meta["name"], table, cols))

            await self._repo.delete_stale_tables(schema.id, active_table_names)

        await self._repo.delete_stale_schemas(data_source_id, active_schema_names)

        if self._embedding_client and self._doc_repo:
            try:
                await self._index_documents(tables_for_indexing)
            except Exception:
                logger.warning("Document indexing failed — catalog data saved without embeddings", exc_info=True)

        return CatalogRefreshResponse(
            data_source_id=data_source_id,
            message="Catalog refreshed successfully.",
            schemas_synced=schemas_synced,
            tables_synced=tables_synced,
            columns_synced=columns_synced,
        )

    async def _index_documents(
        self, tables: list[tuple[str, Table, list[Column]]]
    ) -> None:
        documents: list[TableDocument] = []
        contents: list[str] = []

        for schema_name, table, columns in tables:
            table_content = self._build_table_content(schema_name, table, columns)
            documents.append(TableDocument(
                table_id=table.id,
                document_type="ddl",
                schema_name=schema_name,
                table_name=table.table_name,
                title=f"{schema_name}.{table.table_name}",
                content=table_content,
            ))
            contents.append(table_content)

            for col in columns:
                col_content = self._build_column_content(schema_name, table, col)
                documents.append(TableDocument(
                    table_id=table.id,
                    document_type="ddl",
                    schema_name=schema_name,
                    table_name=table.table_name,
                    column_name=col.column_name,
                    title=f"{schema_name}.{table.table_name}.{col.column_name}",
                    content=col_content,
                ))
                contents.append(col_content)

        embeddings = await self._embedding_client.embed_batch(contents)
        for doc, emb in zip(documents, embeddings):
            doc.embedding = emb

        await self._doc_repo.create_bulk(documents)
        logger.info("Indexed %d documents.", len(documents))

    @staticmethod
    def _effective_description(user_desc: Optional[str], source_desc: Optional[str]) -> str:
        return user_desc or source_desc or "No description"

    @staticmethod
    def _build_table_content(schema_name: str, table: Table, columns: list[Column]) -> str:
        description = table.user_description or table.source_description or "No description"
        col_lines = "\n".join(
            f"  - {c.column_name} ({c.data_type})"
            f"{' PK' if c.is_primary_key else ''}"
            f"{' FK→' + c.references_column if c.is_foreign_key and c.references_column else ''}"
            f"{'' if c.is_nullable else ' NOT NULL'}"
            for c in columns
        )
        return (
            f"Table: {schema_name}.{table.table_name}\n"
            f"Type: {table.table_type}\n"
            f"Row Count: {table.row_count}\n"
            f"Description: {description}\n"
            f"Columns:\n{col_lines}"
        )

    @staticmethod
    def _build_column_content(schema_name: str, table: Table, col: Column) -> str:
        col_desc = col.user_description or col.source_description or "No description"
        table_desc = table.user_description or table.source_description or "No description"
        return (
            f"Column: {schema_name}.{table.table_name}.{col.column_name}\n"
            f"Data Type: {col.data_type}\n"
            f"Description: {col_desc}\n"
            f"Table: {table.table_name} ({table_desc})\n"
            f"Nullable: {col.is_nullable}\n"
            f"Primary Key: {col.is_primary_key}\n"
            f"Foreign Key: {col.is_foreign_key}\n"
            f"References: {col.references_column or 'None'}"
        )

    async def _introspect_postgres(self, config: dict) -> list[dict]:
        conninfo = (
            f"host={config.get('host', 'localhost')} "
            f"port={config.get('port', 5432)} "
            f"dbname={config.get('database', '')} "
            f"user={config.get('username', '')} "
            f"password={config.get('password', '')}"
        )

        result = []

        try:
            async with await psycopg.AsyncConnection.connect(
                conninfo, autocommit=True
            ) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT schema_name FROM information_schema.schemata
                        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                          AND schema_name NOT LIKE 'pg_%'
                        ORDER BY schema_name
                    """)
                    schemas = [row[0] for row in await cur.fetchall()]

                    for schema_name in schemas:
                        schema_meta: dict = {"name": schema_name, "tables": []}

                        # Pre-fetch PK info for the whole schema
                        await cur.execute("""
                            SELECT kcu.table_name, kcu.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                                ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                                AND tc.table_name = kcu.table_name
                            WHERE tc.constraint_type = 'PRIMARY KEY'
                              AND tc.table_schema = %s
                        """, (schema_name,))
                        pk_set: set[tuple[str, str]] = {
                            (r[0], r[1]) for r in await cur.fetchall()
                        }

                        # Pre-fetch FK info for the whole schema
                        await cur.execute("""
                            SELECT
                                kcu.table_name,
                                kcu.column_name,
                                ccu.table_schema || '.' || ccu.table_name || '.' || ccu.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                                ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                                AND tc.table_name = kcu.table_name
                            JOIN information_schema.constraint_column_usage ccu
                                ON ccu.constraint_name = tc.constraint_name
                            WHERE tc.constraint_type = 'FOREIGN KEY'
                              AND tc.table_schema = %s
                        """, (schema_name,))
                        fk_map: dict[tuple[str, str], str] = {
                            (r[0], r[1]): r[2] for r in await cur.fetchall()
                        }

                        # Pre-fetch table comments (COMMENT ON TABLE) for the whole schema
                        await cur.execute("""
                            SELECT c.relname, obj_description(c.oid, 'pg_class')
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE n.nspname = %s
                              AND c.relkind IN ('r', 'v')
                        """, (schema_name,))
                        table_comments: dict[str, Optional[str]] = {
                            r[0]: r[1] for r in await cur.fetchall()
                        }

                        # Pre-fetch column comments for the whole schema
                        await cur.execute("""
                            SELECT c.relname, a.attname, col_description(c.oid, a.attnum)
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            JOIN pg_attribute a ON a.attrelid = c.oid
                            WHERE n.nspname = %s
                              AND c.relkind IN ('r', 'v')
                              AND a.attnum > 0
                              AND NOT a.attisdropped
                        """, (schema_name,))
                        column_comments: dict[tuple[str, str], Optional[str]] = {
                            (r[0], r[1]): r[2] for r in await cur.fetchall()
                        }

                        await cur.execute("""
                            SELECT table_name, table_type
                            FROM information_schema.tables
                            WHERE table_schema = %s
                            ORDER BY table_name
                        """, (schema_name,))
                        tables = await cur.fetchall()

                        for (table_name, raw_type) in tables:
                            table_type = "view" if raw_type == "VIEW" else "table"

                            row_count = 0
                            if table_type == "table":
                                try:
                                    await cur.execute(
                                        "SELECT reltuples::bigint FROM pg_class c "
                                        "JOIN pg_namespace n ON n.oid = c.relnamespace "
                                        "WHERE n.nspname = %s AND c.relname = %s",
                                        (schema_name, table_name),
                                    )
                                    rc = await cur.fetchone()
                                    row_count = max(0, rc[0]) if rc else 0
                                except Exception:
                                    pass

                            await cur.execute("""
                                SELECT column_name, data_type, is_nullable, column_default, ordinal_position
                                FROM information_schema.columns
                                WHERE table_schema = %s AND table_name = %s
                                ORDER BY ordinal_position
                            """, (schema_name, table_name))

                            columns = []
                            for (col_name, data_type, is_nullable, default_val, ordinal) in await cur.fetchall():
                                columns.append({
                                    "column_name": col_name,
                                    "data_type": data_type,
                                    "ordinal_position": ordinal,
                                    "is_nullable": is_nullable == "YES",
                                    "default_value": default_val,
                                    "is_primary_key": (table_name, col_name) in pk_set,
                                    "is_foreign_key": (table_name, col_name) in fk_map,
                                    "references_column": fk_map.get((table_name, col_name)),
                                    "source_description": column_comments.get((table_name, col_name)),
                                })

                            schema_meta["tables"].append({
                                "name": table_name,
                                "type": table_type,
                                "row_count": row_count,
                                "source_description": table_comments.get(table_name),
                                "columns": columns,
                            })

                        result.append(schema_meta)

        except psycopg.OperationalError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot connect to database: {e}",
            )

        return result

    # ── Response converters ────────────────────────────────────────────────────

    def _table_to_response(self, table: Table, schema_name: str) -> TableResponse:
        return TableResponse(
            id=table.id,
            schema_id=table.schema_id,
            schema_name=schema_name,
            table_name=table.table_name,
            table_type=table.table_type,
            row_count=table.row_count,
            source_description=table.source_description,
            user_description=table.user_description,
            tags=table.tags,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )

    def _column_to_response(self, column: Column) -> ColumnResponse:
        return ColumnResponse(
            id=column.id,
            column_name=column.column_name,
            data_type=column.data_type,
            is_nullable=column.is_nullable,
            default_value=column.default_value,
            is_primary_key=column.is_primary_key,
            is_foreign_key=column.is_foreign_key,
            references_column=column.references_column,
            source_description=column.source_description,
            user_description=column.user_description,
            ordinal_position=column.ordinal_position,
        )

    # ── Semantic search (merged from DataDiscoveryService) ────────────────────

    async def semantic_search(self, request: SemanticSearchRequest) -> SemanticSearchResponse:
        import time
        if self._embedding_client is None or self._doc_repo is None:
            raise HTTPException(status_code=503, detail="Embedding service not available.")

        start_ms = time.monotonic() * 1000
        query_embedding = await self._embedding_client.embed(request.query)

        table_only = request.search_type == "tables"
        column_only = request.search_type == "columns"
        schema_filter = request.filters.schema_name if request.filters else None

        rows = await self._doc_repo.semantic_search(
            query_embedding,
            schema_name=schema_filter,
            table_only=table_only,
            column_only=column_only,
            limit=request.limit,
        )

        results = [self._doc_to_semantic_result(doc, score) for doc, score in rows]
        elapsed_ms = int(time.monotonic() * 1000 - start_ms)

        if self._history_repo:
            try:
                await self._history_repo.create(
                    query=request.query,
                    search_type="semantic",
                    results_count=len(results),
                    search_time_ms=elapsed_ms,
                )
            except Exception:
                logger.warning("Failed to save search history", exc_info=True)

        return SemanticSearchResponse(
            query=request.query,
            results=results,
            total_found=len(results),
            search_time_ms=elapsed_ms,
        )

    async def find_similar(self, request: SimilarTableRequest) -> SemanticSearchResponse:
        if self._doc_repo is None:
            raise HTTPException(status_code=503, detail="Embedding service not available.")

        docs = await self._doc_repo.find_by_table_id(request.table_id)
        table_doc = next((d for d in docs if d.column_name is None), None)

        if table_doc is None or table_doc.embedding is None:
            raise HTTPException(
                status_code=404,
                detail="No embedding found for the specified table. Run catalog refresh first.",
            )

        rows = await self._doc_repo.semantic_search(
            table_doc.embedding,
            table_only=True,
            limit=request.limit + 1,
            min_similarity=0.5,
        )

        results = [
            self._doc_to_semantic_result(doc, score)
            for doc, score in rows
            if doc.table_id != request.table_id
        ][: request.limit]

        return SemanticSearchResponse(
            query=f"similar:{table_doc.table_name}",
            results=results,
            total_found=len(results),
            search_time_ms=0,
        )

    async def get_recommendations(self, query: str) -> RecommendationResponse:
        if not query or self._embedding_client is None or self._doc_repo is None:
            return RecommendationResponse(query=query, recommended_tables=[], suggested_questions=[])

        query_embedding = await self._embedding_client.embed(query)
        rows = await self._doc_repo.semantic_search(
            query_embedding, table_only=True, limit=5, min_similarity=0.4
        )

        recommended = [
            RecommendedTable(
                table_id=doc.table_id,
                table_name=doc.table_name,
                schema_name=doc.schema_name,
                reason="Semantically similar to your query",
                confidence=round(score, 3),
            )
            for doc, score in rows
        ]

        return RecommendationResponse(
            query=query,
            recommended_tables=recommended,
            suggested_questions=[],
        )

    async def get_search_history(self, limit: int = 50) -> list[SearchHistoryItem]:
        if self._history_repo is None:
            return []
        entries = await self._history_repo.list(limit)
        return [SearchHistoryItem.model_validate(e) for e in entries]

    @staticmethod
    def _doc_to_semantic_result(doc, score: float) -> SemanticSearchResultItem:
        result_type = "column" if doc.column_name else "table"
        snippet = doc.content[:200].replace("\n", " ").strip()
        return SemanticSearchResultItem(
            type=result_type,
            table_id=doc.table_id,
            schema_name=doc.schema_name,
            table_name=doc.table_name,
            column_name=doc.column_name,
            description=doc.title,
            relevance_score=round(score, 4),
            snippet=snippet,
        )
