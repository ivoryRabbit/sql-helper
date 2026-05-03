import logging
import os
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import psycopg
from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class CatalogSyncActivityInput:
    data_source_id: str
    metadata: list


def _get_db_url() -> str:
    host = os.getenv("DB_HOST", "0.0.0.0")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "sqlhelper")
    password = os.getenv("DB_PASSWORD", "sqlhelper")
    name = os.getenv("DB_NAME", "vectordb")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


async def _get_session():
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(_get_db_url(), echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


@activity.defn
async def introspect_postgres(config: dict) -> list:
    conninfo = (
        f"host={config.get('host', 'localhost')} "
        f"port={config.get('port', 5432)} "
        f"dbname={config.get('database', '')} "
        f"user={config.get('username', '')} "
        f"password={config.get('password', '')}"
    )

    result = []
    async with await psycopg.AsyncConnection.connect(conninfo, autocommit=True) as conn:
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

                await cur.execute("""
                    SELECT kcu.table_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                        AND tc.table_name = kcu.table_name
                    WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = %s
                """, (schema_name,))
                pk_set: set = {(r[0], r[1]) for r in await cur.fetchall()}

                await cur.execute("""
                    SELECT kcu.table_name, kcu.column_name,
                           ccu.table_schema || '.' || ccu.table_name || '.' || ccu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                        AND tc.table_name = kcu.table_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s
                """, (schema_name,))
                fk_map: dict = {(r[0], r[1]): r[2] for r in await cur.fetchall()}

                await cur.execute("""
                    SELECT c.relname, obj_description(c.oid, 'pg_class')
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = %s AND c.relkind IN ('r', 'v')
                """, (schema_name,))
                table_comments: dict = {r[0]: r[1] for r in await cur.fetchall()}

                await cur.execute("""
                    SELECT c.relname, a.attname, col_description(c.oid, a.attnum)
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_attribute a ON a.attrelid = c.oid
                    WHERE n.nspname = %s AND c.relkind IN ('r', 'v')
                      AND a.attnum > 0 AND NOT a.attisdropped
                """, (schema_name,))
                column_comments: dict = {(r[0], r[1]): r[2] for r in await cur.fetchall()}

                await cur.execute("""
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = %s ORDER BY table_name
                """, (schema_name,))

                for (table_name, raw_type) in await cur.fetchall():
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

    logger.info("Introspected %d schemas", len(result))
    return result


@activity.defn
async def upsert_catalog_data(input: CatalogSyncActivityInput) -> dict:
    from uuid import UUID as _UUID

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from repositories.data_catalog import DataCatalogRepository

    engine = create_async_engine(_get_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    data_source_id = _UUID(input.data_source_id)
    schemas_synced = tables_synced = columns_synced = 0

    async with async_session() as session:
        repo = DataCatalogRepository(session)
        active_schema_names = [sm["name"] for sm in input.metadata]

        for schema_meta in input.metadata:
            schema = await repo.upsert_schema(data_source_id, schema_meta["name"])
            schemas_synced += 1

            active_table_names = [tm["name"] for tm in schema_meta["tables"]]
            for table_meta in schema_meta["tables"]:
                table = await repo.upsert_table(
                    schema_id=schema.id,
                    table_name=table_meta["name"],
                    table_type=table_meta["type"],
                    row_count=table_meta["row_count"],
                    source_description=table_meta.get("source_description"),
                )
                tables_synced += 1

                active_col_names = [cm["column_name"] for cm in table_meta["columns"]]
                for col_meta in table_meta["columns"]:
                    await repo.upsert_column(table_id=table.id, **col_meta)
                    columns_synced += 1
                await repo.delete_stale_columns(table.id, active_col_names)

            await repo.delete_stale_tables(schema.id, active_table_names)

        await repo.delete_stale_schemas(data_source_id, active_schema_names)
        await session.commit()

    await engine.dispose()

    logger.info(
        "Upserted catalog: data_source=%s schemas=%d tables=%d columns=%d",
        input.data_source_id, schemas_synced, tables_synced, columns_synced,
    )
    return {
        "schemas_synced": schemas_synced,
        "tables_synced": tables_synced,
        "columns_synced": columns_synced,
    }


@activity.defn
async def generate_catalog_embeddings(data_source_id: str) -> int:
    from uuid import UUID as _UUID

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from clients.embedding import EmbeddingClient
    from configs.settings import Settings
    from models.entities import TableDocument
    from repositories.data_catalog import DataCatalogRepository
    from repositories.table_document import TableDocumentRepository
    from services.data_catalog import DataCatalogService

    settings = Settings()
    engine = create_async_engine(_get_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ds_id = _UUID(data_source_id)
    documents_indexed = 0

    async with async_session() as session:
        catalog_repo = DataCatalogRepository(session)
        doc_repo = TableDocumentRepository(session)
        embedding_client = EmbeddingClient(model_name=settings.embedding_model)

        schemas = await catalog_repo.get_schemas_by_source(ds_id)

        # Wipe existing documents before re-indexing
        if schemas:
            await doc_repo.delete_by_schema_names([s.schema_name for s in schemas])

        tables_for_indexing = []
        for schema in schemas:
            tables = await catalog_repo.get_tables_by_schema(schema.id)
            for table in tables:
                columns = await catalog_repo.get_columns_by_table(table.id)
                tables_for_indexing.append((schema.schema_name, table, columns))

        if tables_for_indexing:
            documents: list[TableDocument] = []
            contents: list[str] = []

            for schema_name, table, columns in tables_for_indexing:
                table_content = DataCatalogService._build_table_content(schema_name, table, columns)
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
                    col_content = DataCatalogService._build_column_content(schema_name, table, col)
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

            embeddings = await embedding_client.embed_batch(contents)
            for doc, emb in zip(documents, embeddings):
                doc.embedding = emb

            await doc_repo.create_bulk(documents)
            documents_indexed = len(documents)
            await session.commit()

    await engine.dispose()
    logger.info("Generated %d embeddings for data_source=%s", documents_indexed, data_source_id)
    return documents_indexed
