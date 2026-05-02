import csv
import io
import json
import logging
import statistics
import time
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from adapters.postgres import PostgresAdapter
from adapters.redshift import RedshiftAdapter
from adapters.trino import TrinoAdapter
from clients.storage import StorageClient
from models.request.data_analysis import AnalysisExecuteRequest, DataExportRequest
from models.response.data_analysis import (
    AnalysisExecutionResponse,
    AnalysisHistoryItem,
    ColumnInfo,
    ColumnStats,
    ExportResponse,
    InsightItem,
    VisualizationConfig,
)
from repositories.data_analysis import (
    AnalysisExecutionRepository,
    AnalysisInsightRepository,
    AnalysisResultRepository,
)
from repositories.data_source import DataSourceRepository
from utils.crypto import EncryptionService

_ADAPTERS = {
    "postgresql": PostgresAdapter(),
    "redshift": RedshiftAdapter(),
    "trino": TrinoAdapter(),
}

logger = logging.getLogger(__name__)

_SENSITIVE_FIELDS = {"password"}

_NUMERIC_TYPE_HINTS = frozenset({
    "integer", "bigint", "smallint", "real", "double precision",
    "numeric", "float", "int", "int2", "int4", "int8",
})
_DATE_TYPE_HINTS = frozenset({"date", "time", "timestamp", "timestamptz"})

_EXPORT_BUCKET = "exports"
_EXPORT_CONTENT_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
}


class DataAnalysisService:
    def __init__(
        self,
        execution_repo: AnalysisExecutionRepository,
        result_repo: AnalysisResultRepository,
        insight_repo: AnalysisInsightRepository,
        data_source_repo: DataSourceRepository,
        encryption: EncryptionService,
        storage: StorageClient,
    ) -> None:
        self._exec_repo = execution_repo
        self._result_repo = result_repo
        self._insight_repo = insight_repo
        self._ds_repo = data_source_repo
        self._enc = encryption
        self._storage = storage

    # ── Public API ────────────────────────────────────────────────────────────

    async def execute(self, request: AnalysisExecuteRequest) -> AnalysisExecutionResponse:
        source = await self._ds_repo.get(request.data_source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Data source not found")

        config = self._decrypt_config(dict(source.config))
        adapter = _ADAPTERS.get(source.type)
        if adapter is None:
            raise HTTPException(status_code=400, detail=f"Unsupported data source type: {source.type}")

        execution = await self._exec_repo.create(
            sql_generation_id=request.sql_generation_id,
            data_source_id=request.data_source_id,
            executed_sql=request.sql,
            status="running",
        )

        logger.info(
            "Executing query: execution_id=%s data_source=%s sql=%r",
            execution.id, source.name, request.sql[:120],
        )
        try:
            start = time.monotonic()
            rows, raw_columns = await adapter.execute_query(
                config, request.sql, limit=request.options.limit_rows
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
        except ValueError as exc:
            logger.warning("Query rejected: execution_id=%s error=%s", execution.id, exc)
            await self._exec_repo.update(execution.id, status="failed", error_message=str(exc))
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("Query execution failed: execution_id=%s error=%s", execution.id, exc, exc_info=True)
            await self._exec_repo.update(execution.id, status="failed", error_message=str(exc))
            raise HTTPException(status_code=502, detail=f"Query execution failed: {exc}")

        columns = [ColumnInfo(**c) for c in raw_columns]
        # Store a preview (first 100 rows) in JSONB
        preview_rows = _serialize_rows(rows[:100])

        logger.info(
            "Query completed: execution_id=%s rows=%d elapsed_ms=%d",
            execution.id, len(rows), elapsed_ms,
        )
        await self._exec_repo.update(
            execution.id,
            execution_time_ms=elapsed_ms,
            row_count=len(rows),
            status="completed",
            result_preview={"columns": raw_columns, "rows": preview_rows},
        )

        stats: list[ColumnStats] = []
        insights: list[InsightItem] = []
        visualizations: list[VisualizationConfig] = []

        if request.options.include_statistics and rows:
            stats = self._compute_statistics(rows, raw_columns)
            for col_stat in stats:
                await self._result_repo.create(
                    analysis_id=execution.id,
                    column_name=col_stat.column_name,
                    data_type=col_stat.data_type,
                    null_count=col_stat.null_count,
                    unique_count=col_stat.unique_count,
                    min_value=col_stat.min_value,
                    max_value=col_stat.max_value,
                    avg_value=col_stat.avg_value,
                    summary_stats=col_stat.summary_stats,
                )

        if request.options.generate_insights and stats:
            insights = self._generate_insights(stats, len(rows))
            for item in insights:
                await self._insight_repo.create(
                    analysis_id=execution.id,
                    insight_type=item.insight_type,
                    insight_text=item.insight_text,
                    confidence_score=item.confidence_score,
                )

            visualizations = self._recommend_visualizations(raw_columns, rows)

        return AnalysisExecutionResponse(
            id=execution.id,
            sql_generation_id=execution.sql_generation_id,
            data_source_id=execution.data_source_id,
            executed_sql=execution.executed_sql,
            execution_time_ms=elapsed_ms,
            row_count=len(rows),
            status="completed",
            error_message=None,
            columns=columns,
            data=_serialize_rows(rows),
            statistics=stats,
            insights=insights,
            visualizations=visualizations,
            created_at=execution.created_at,
        )

    async def get_result(self, analysis_id: UUID) -> AnalysisExecutionResponse:
        execution = await self._exec_repo.get(analysis_id)
        if execution is None:
            raise HTTPException(status_code=404, detail="Analysis not found")

        result_rows = await self._result_repo.get_by_analysis(analysis_id)
        insight_rows = await self._insight_repo.get_by_analysis(analysis_id)

        preview = execution.result_preview or {}
        raw_columns: list[dict] = preview.get("columns", [])
        raw_rows: list[dict] = preview.get("rows", [])

        stats = [
            ColumnStats(
                column_name=r.column_name or "",
                data_type=r.data_type or "",
                null_count=r.null_count or 0,
                unique_count=r.unique_count or 0,
                total_count=execution.row_count or 0,
                min_value=r.min_value,
                max_value=r.max_value,
                avg_value=r.avg_value,
                summary_stats=r.summary_stats,
            )
            for r in result_rows
        ]
        insights = [
            InsightItem(
                insight_type=i.insight_type,
                insight_text=i.insight_text,
                confidence_score=i.confidence_score,
            )
            for i in insight_rows
        ]
        visualizations = self._recommend_visualizations(raw_columns, raw_rows) if raw_columns else []

        return AnalysisExecutionResponse(
            id=execution.id,
            sql_generation_id=execution.sql_generation_id,
            data_source_id=execution.data_source_id,
            executed_sql=execution.executed_sql,
            execution_time_ms=execution.execution_time_ms,
            row_count=execution.row_count,
            status=execution.status,
            error_message=execution.error_message,
            columns=[ColumnInfo(**c) for c in raw_columns],
            data=raw_rows,
            statistics=stats,
            insights=insights,
            visualizations=visualizations,
            created_at=execution.created_at,
        )

    async def get_history(self, limit: int = 50) -> list[AnalysisHistoryItem]:
        rows = await self._exec_repo.list_recent(limit)
        return [AnalysisHistoryItem.model_validate(r) for r in rows]

    async def export(self, request: DataExportRequest) -> ExportResponse:
        execution = await self._exec_repo.get(request.analysis_id)
        if execution is None:
            raise HTTPException(status_code=404, detail="Analysis not found")
        if execution.status != "completed":
            raise HTTPException(status_code=409, detail="Analysis has not completed successfully")

        preview = execution.result_preview or {}
        raw_columns: list[dict] = preview.get("columns", [])
        rows: list[dict] = preview.get("rows", [])

        content: bytes
        if request.format == "csv":
            content = self._to_csv(rows, raw_columns, execution, request.include_metadata)
        else:
            content = self._to_json(rows, raw_columns, execution, request.include_metadata)

        await self._storage.create_bucket_if_not_exists(_EXPORT_BUCKET)
        key = f"{execution.id}.{request.format}"
        await self._storage.upload(
            _EXPORT_BUCKET,
            key,
            content,
            content_type=_EXPORT_CONTENT_TYPES[request.format],
        )
        url = await self._storage.presigned_url(_EXPORT_BUCKET, key, expires_seconds=3600)

        return ExportResponse(
            analysis_id=request.analysis_id,
            format=request.format,
            download_url=url,
            expires_in_seconds=3600,
        )

    # ── Statistics ────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_statistics(rows: list[dict], raw_columns: list[dict]) -> list[ColumnStats]:
        total = len(rows)
        result: list[ColumnStats] = []

        for col in raw_columns:
            name = col["name"]
            dtype = col["type"].lower()
            values = [row.get(name) for row in rows]
            non_null = [v for v in values if v is not None]

            null_count = total - len(non_null)
            unique_count = len(set(str(v) for v in non_null))

            min_val = max_val = avg_val = None
            summary: dict = {}

            if non_null:
                is_numeric = any(hint in dtype for hint in _NUMERIC_TYPE_HINTS)
                is_date = any(hint in dtype for hint in _DATE_TYPE_HINTS)

                if is_numeric:
                    floats: list[float] = []
                    for v in non_null:
                        try:
                            floats.append(float(v))
                        except (TypeError, ValueError):
                            pass
                    if floats:
                        min_val = str(min(floats))
                        max_val = str(max(floats))
                        avg_val = sum(floats) / len(floats)
                        summary = {
                            "mean": avg_val,
                            "std_dev": statistics.stdev(floats) if len(floats) > 1 else 0.0,
                        }
                        if len(floats) >= 4:
                            sorted_f = sorted(floats)
                            n = len(sorted_f)
                            summary["q1"] = sorted_f[n // 4]
                            summary["median"] = statistics.median(floats)
                            summary["q3"] = sorted_f[(3 * n) // 4]
                elif is_date:
                    str_vals = [str(v) for v in non_null]
                    min_val = min(str_vals)
                    max_val = max(str_vals)
                else:
                    # text / other
                    str_vals = [str(v) for v in non_null]
                    lengths = [len(s) for s in str_vals]
                    min_val = str(min(lengths))
                    max_val = str(max(lengths))
                    avg_val = sum(lengths) / len(lengths)
                    # most common values
                    freq: dict[str, int] = {}
                    for s in str_vals:
                        freq[s] = freq.get(s, 0) + 1
                    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
                    summary["most_common"] = [{"value": v, "count": c} for v, c in top]

            result.append(ColumnStats(
                column_name=name,
                data_type=dtype,
                null_count=null_count,
                unique_count=unique_count,
                total_count=total,
                min_value=min_val,
                max_value=max_val,
                avg_value=avg_val,
                summary_stats=summary if summary else None,
            ))

        return result

    # ── Insights ──────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_insights(stats: list[ColumnStats], total_rows: int) -> list[InsightItem]:
        insights: list[InsightItem] = []

        for col in stats:
            if total_rows == 0:
                continue

            null_pct = (col.null_count / total_rows) * 100

            # High null rate
            if null_pct > 50:
                insights.append(InsightItem(
                    insight_type="data_quality",
                    insight_text=(
                        f"Column '{col.column_name}' has {null_pct:.1f}% null values. "
                        "Consider investigating missing data or imputation."
                    ),
                    confidence_score=0.9,
                ))
            elif null_pct > 20:
                insights.append(InsightItem(
                    insight_type="data_quality",
                    insight_text=f"Column '{col.column_name}' has {null_pct:.1f}% null values.",
                    confidence_score=0.7,
                ))

            # Low cardinality text
            dtype = col.data_type.lower()
            is_text = any(t in dtype for t in ("text", "varchar", "char"))
            if is_text and col.unique_count < 10 and total_rows >= 20:
                insights.append(InsightItem(
                    insight_type="pattern",
                    insight_text=(
                        f"Column '{col.column_name}' has only {col.unique_count} unique values "
                        "— consider treating it as a categorical variable."
                    ),
                    confidence_score=0.75,
                ))

            # Numeric outlier detection via IQR
            is_numeric = any(h in dtype for h in _NUMERIC_TYPE_HINTS)
            if is_numeric and col.summary_stats and "q1" in col.summary_stats:
                q1 = col.summary_stats["q1"]
                q3 = col.summary_stats["q3"]
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    if col.min_value and float(col.min_value) < lower:
                        insights.append(InsightItem(
                            insight_type="outlier",
                            insight_text=(
                                f"Column '{col.column_name}' has values below the lower IQR fence "
                                f"({lower:.2f}). Review for data quality issues."
                            ),
                            confidence_score=0.8,
                        ))
                    if col.max_value and float(col.max_value) > upper:
                        insights.append(InsightItem(
                            insight_type="outlier",
                            insight_text=(
                                f"Column '{col.column_name}' has values above the upper IQR fence "
                                f"({upper:.2f}). Review for data quality issues."
                            ),
                            confidence_score=0.8,
                        ))

        # Row count insight
        if total_rows == 0:
            insights.append(InsightItem(
                insight_type="general",
                insight_text="The query returned no rows.",
                confidence_score=1.0,
            ))

        return insights

    # ── Visualizations ────────────────────────────────────────────────────────

    @staticmethod
    def _recommend_visualizations(
        raw_columns: list[dict], rows: list[dict]
    ) -> list[VisualizationConfig]:
        if not rows or not raw_columns:
            return []

        numeric_cols = [
            c["name"] for c in raw_columns
            if any(h in c["type"].lower() for h in _NUMERIC_TYPE_HINTS)
        ]
        date_cols = [
            c["name"] for c in raw_columns
            if any(h in c["type"].lower() for h in _DATE_TYPE_HINTS)
        ]
        text_cols = [
            c["name"] for c in raw_columns
            if any(t in c["type"].lower() for t in ("text", "varchar", "char"))
            and c["name"] not in date_cols
        ]

        vizs: list[VisualizationConfig] = []

        # Time series: date × numeric
        for date_col in date_cols[:2]:
            for num_col in numeric_cols[:3]:
                vizs.append(VisualizationConfig(
                    type="line_chart",
                    title=f"{num_col} over {date_col}",
                    config={"x_axis": date_col, "y_axis": num_col},
                ))

        # Bar chart: categorical × numeric (first 3 unique text cols)
        low_cardinality_text = [
            col for col in text_cols[:3]
            if len({str(r.get(col)) for r in rows}) <= 50
        ]
        for cat_col in low_cardinality_text[:2]:
            for num_col in numeric_cols[:2]:
                vizs.append(VisualizationConfig(
                    type="bar_chart",
                    title=f"{num_col} by {cat_col}",
                    config={"x_axis": cat_col, "y_axis": num_col},
                ))

        # Scatter: first two numeric columns
        if len(numeric_cols) >= 2:
            vizs.append(VisualizationConfig(
                type="scatter_plot",
                title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                config={"x_axis": numeric_cols[0], "y_axis": numeric_cols[1]},
            ))

        # Always include a table view
        vizs.append(VisualizationConfig(
            type="table",
            title="Result Table",
            config={"columns": [c["name"] for c in raw_columns]},
        ))

        return vizs

    # ── Export helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _to_csv(
        rows: list[dict],
        raw_columns: list[dict],
        execution: Any,
        include_metadata: bool,
    ) -> bytes:
        buf = io.StringIO()
        if include_metadata:
            buf.write(f"# analysis_id: {execution.id}\n")
            buf.write(f"# executed_sql: {execution.executed_sql.replace(chr(10), ' ')}\n")
            buf.write(f"# execution_time_ms: {execution.execution_time_ms}\n")
            buf.write(f"# row_count: {execution.row_count}\n")
            buf.write(f"# created_at: {execution.created_at}\n")
        if rows:
            writer = csv.DictWriter(buf, fieldnames=[c["name"] for c in raw_columns])
            writer.writeheader()
            writer.writerows(rows)
        return buf.getvalue().encode("utf-8")

    @staticmethod
    def _to_json(
        rows: list[dict],
        raw_columns: list[dict],
        execution: Any,
        include_metadata: bool,
    ) -> bytes:
        payload: dict = {"data": rows}
        if include_metadata:
            payload["metadata"] = {
                "analysis_id": str(execution.id),
                "executed_sql": execution.executed_sql,
                "execution_time_ms": execution.execution_time_ms,
                "row_count": execution.row_count,
                "columns": raw_columns,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
            }
        return json.dumps(payload, default=str, ensure_ascii=False, indent=2).encode("utf-8")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _decrypt_config(self, config: dict) -> dict:
        for field in _SENSITIVE_FIELDS:
            if field in config and config[field]:
                try:
                    config[field] = self._enc.decrypt(config[field])
                except Exception:
                    pass
        return config
