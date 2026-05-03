import logging
import os
import statistics
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from temporalio import activity

logger = logging.getLogger(__name__)

_NUMERIC_TYPE_HINTS = frozenset({
    "integer", "bigint", "smallint", "real", "double precision",
    "numeric", "float", "int", "int2", "int4", "int8",
})


@dataclass
class AnalysisExecutionInput:
    execution_id: str
    data_source_id: str
    sql: str
    limit_rows: int = 1000


def _get_db_url() -> str:
    host = os.getenv("DB_HOST", "0.0.0.0")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "sqlhelper")
    password = os.getenv("DB_PASSWORD", "sqlhelper")
    name = os.getenv("DB_NAME", "vectordb")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


@activity.defn
async def execute_and_store_query(input: AnalysisExecutionInput) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from adapters.postgres import PostgresAdapter
    from adapters.redshift import RedshiftAdapter
    from adapters.trino import TrinoAdapter
    from configs.settings import Settings
    from repositories.data_analysis import AnalysisExecutionRepository
    from repositories.data_source import DataSourceRepository
    from utils.crypto import EncryptionService

    _ADAPTERS = {
        "postgresql": PostgresAdapter(),
        "redshift": RedshiftAdapter(),
        "trino": TrinoAdapter(),
    }

    settings = Settings()
    enc = EncryptionService(key=settings.encryption_key)

    engine = create_async_engine(_get_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ds_repo = DataSourceRepository(session)
        exec_repo = AnalysisExecutionRepository(session)

        source = await ds_repo.get(UUID(input.data_source_id))
        if source is None:
            await exec_repo.update(UUID(input.execution_id), status="failed", error_message="Data source not found")
            await session.commit()
            raise ValueError(f"Data source {input.data_source_id} not found")

        config = dict(source.config)
        if "password" in config and config["password"]:
            try:
                config["password"] = enc.decrypt(config["password"])
            except Exception:
                pass

        adapter = _ADAPTERS.get(source.type)
        if adapter is None:
            msg = f"Unsupported data source type: {source.type}"
            await exec_repo.update(UUID(input.execution_id), status="failed", error_message=msg)
            await session.commit()
            raise ValueError(msg)

        try:
            start = time.monotonic()
            rows, raw_columns = await adapter.execute_query(config, input.sql, limit=input.limit_rows)
            elapsed_ms = int((time.monotonic() - start) * 1000)
        except Exception as exc:
            msg = str(exc)
            logger.error("Query failed: execution_id=%s error=%s", input.execution_id, msg)
            await exec_repo.update(UUID(input.execution_id), status="failed", error_message=msg)
            await session.commit()
            raise

        preview_rows = _serialize_rows(rows[:100])
        await exec_repo.update(
            UUID(input.execution_id),
            execution_time_ms=elapsed_ms,
            row_count=len(rows),
            status="completed",
            result_preview={"columns": raw_columns, "rows": preview_rows},
        )
        await session.commit()

    await engine.dispose()
    logger.info("execute_and_store_query done: execution_id=%s rows=%d ms=%d", input.execution_id, len(rows), elapsed_ms)
    return {"row_count": len(rows), "execution_time_ms": elapsed_ms}


@activity.defn
async def compute_and_store_stats(execution_id: str) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from repositories.data_analysis import AnalysisExecutionRepository, AnalysisResultRepository

    engine = create_async_engine(_get_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        exec_repo = AnalysisExecutionRepository(session)
        result_repo = AnalysisResultRepository(session)

        execution = await exec_repo.get(UUID(execution_id))
        if execution is None or not execution.result_preview:
            return

        preview = execution.result_preview
        raw_columns = preview.get("columns", [])
        rows = preview.get("rows", [])

        for col_meta in raw_columns:
            col_name = col_meta["name"]
            col_type = col_meta.get("type", "")
            values = [r[col_name] for r in rows if r.get(col_name) is not None]

            null_count = sum(1 for r in rows if r.get(col_name) is None)
            unique_count = len(set(str(v) for v in values))
            min_val = max_val = avg_val = None
            summary_stats = None

            is_numeric = any(h in col_type.lower() for h in _NUMERIC_TYPE_HINTS)
            if is_numeric and values:
                numeric_values = []
                for v in values:
                    try:
                        numeric_values.append(float(v))
                    except (TypeError, ValueError):
                        pass
                if numeric_values:
                    min_val = str(min(numeric_values))
                    max_val = str(max(numeric_values))
                    avg_val = str(sum(numeric_values) / len(numeric_values))
                    if len(numeric_values) >= 4:
                        sorted_v = sorted(numeric_values)
                        n = len(sorted_v)
                        q1 = sorted_v[n // 4]
                        q3 = sorted_v[(3 * n) // 4]
                        summary_stats = {
                            "q1": q1,
                            "median": statistics.median(sorted_v),
                            "q3": q3,
                            "std": statistics.stdev(sorted_v) if len(sorted_v) >= 2 else 0,
                        }

            await result_repo.create(
                analysis_id=UUID(execution_id),
                column_name=col_name,
                data_type=col_type,
                null_count=null_count,
                unique_count=unique_count,
                min_value=min_val,
                max_value=max_val,
                avg_value=avg_val,
                summary_stats=summary_stats,
            )

        await session.commit()

    await engine.dispose()
    logger.info("compute_and_store_stats done: execution_id=%s cols=%d", execution_id, len(raw_columns))


@activity.defn
async def generate_and_store_insights(execution_id: str) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from repositories.data_analysis import (
        AnalysisExecutionRepository,
        AnalysisInsightRepository,
        AnalysisResultRepository,
    )

    engine = create_async_engine(_get_db_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        exec_repo = AnalysisExecutionRepository(session)
        result_repo = AnalysisResultRepository(session)
        insight_repo = AnalysisInsightRepository(session)

        execution = await exec_repo.get(UUID(execution_id))
        if execution is None:
            return

        total_rows = execution.row_count or 0
        col_stats = await result_repo.get_by_analysis(UUID(execution_id))

        for col in col_stats:
            if total_rows == 0:
                continue

            null_pct = (col.null_count / total_rows) * 100

            if null_pct > 50:
                await insight_repo.create(
                    analysis_id=UUID(execution_id),
                    insight_type="data_quality",
                    insight_text=(
                        f"Column '{col.column_name}' has {null_pct:.1f}% null values. "
                        "Consider investigating missing data or imputation."
                    ),
                    confidence_score=0.9,
                )
            elif null_pct > 20:
                await insight_repo.create(
                    analysis_id=UUID(execution_id),
                    insight_type="data_quality",
                    insight_text=f"Column '{col.column_name}' has {null_pct:.1f}% null values.",
                    confidence_score=0.7,
                )

            dtype = (col.data_type or "").lower()
            is_text = any(t in dtype for t in ("text", "varchar", "char"))
            if is_text and col.unique_count < 10 and total_rows >= 20:
                await insight_repo.create(
                    analysis_id=UUID(execution_id),
                    insight_type="pattern",
                    insight_text=(
                        f"Column '{col.column_name}' has only {col.unique_count} unique values "
                        "— consider treating it as a categorical variable."
                    ),
                    confidence_score=0.75,
                )

            is_numeric = any(h in dtype for h in _NUMERIC_TYPE_HINTS)
            if is_numeric and col.summary_stats and "q1" in col.summary_stats:
                q1 = col.summary_stats["q1"]
                q3 = col.summary_stats["q3"]
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    if col.min_value and float(col.min_value) < lower:
                        await insight_repo.create(
                            analysis_id=UUID(execution_id),
                            insight_type="outlier",
                            insight_text=(
                                f"Column '{col.column_name}' has values below the lower IQR fence "
                                f"({lower:.2f}). Review for data quality issues."
                            ),
                            confidence_score=0.8,
                        )
                    if col.max_value and float(col.max_value) > upper:
                        await insight_repo.create(
                            analysis_id=UUID(execution_id),
                            insight_type="outlier",
                            insight_text=(
                                f"Column '{col.column_name}' has values above the upper IQR fence "
                                f"({upper:.2f}). Review for data quality issues."
                            ),
                            confidence_score=0.8,
                        )

        if total_rows == 0:
            await insight_repo.create(
                analysis_id=UUID(execution_id),
                insight_type="general",
                insight_text="The query returned no rows.",
                confidence_score=1.0,
            )

        await session.commit()

    await engine.dispose()
    logger.info("generate_and_store_insights done: execution_id=%s", execution_id)


def _serialize_rows(rows: list[Any]) -> list[dict]:
    result = []
    for row in rows:
        if isinstance(row, dict):
            result.append({k: str(v) if v is not None else None for k, v in row.items()})
        else:
            result.append(row)
    return result
