from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from components.database_manager import ModelBase


class DataSource(ModelBase):
    __tablename__ = "data_sources"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # postgresql | redshift | trino
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # JSONB with sensitive fields (e.g. password) encrypted by EncryptionService
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # connected | disconnected | error
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="disconnected"
    )
    last_synced: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Schema(ModelBase):
    __tablename__ = "schemas"
    __table_args__ = (UniqueConstraint("data_source_id", "schema_name"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    data_source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.data_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    schema_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Table(ModelBase):
    __tablename__ = "tables"
    __table_args__ = (UniqueConstraint("schema_id", "table_name"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    schema_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.schemas.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # table | view
    table_type: Mapped[str] = mapped_column(String(20), nullable=False, default="table")
    row_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    # pulled from DB COMMENT ON TABLE; overwritten on every sync
    source_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # written by the user via the UI; never overwritten by sync
    user_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Column(ModelBase):
    __tablename__ = "columns"
    __table_args__ = (UniqueConstraint("table_id", "column_name"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    table_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.tables.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_foreign_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    references_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # pulled from pg_description; overwritten on every sync
    source_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # written by the user via the UI; never overwritten by sync
    user_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ordinal_position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TableDocument(ModelBase):
    __tablename__ = "table_documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    # FK not enforced — documents can outlive catalog rows during refresh
    table_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    # ddl | doc | example
    document_type: Mapped[str] = mapped_column(String(10), nullable=False)
    schema_name: Mapped[str] = mapped_column(String(255), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SearchHistory(ModelBase):
    __tablename__ = "search_history"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    search_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    results_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    search_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ConversationSession(ModelBase):
    __tablename__ = "conversation_sessions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    data_source_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.data_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SqlGeneration(ModelBase):
    __tablename__ = "sql_generations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    data_source_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.data_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    selected_tables: Mapped[Optional[list[UUID]]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)), nullable=True
    )
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_plan: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # pending | valid | invalid
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    validation_errors: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnalysisExecution(ModelBase):
    __tablename__ = "analysis_executions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    sql_generation_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.sql_generations.id", ondelete="SET NULL"),
        nullable=True,
    )
    data_source_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.data_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    executed_sql: Mapped[str] = mapped_column(Text, nullable=False)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # running | completed | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Serialized result rows (limited preview, JSON array)
    result_preview: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnalysisResult(ModelBase):
    __tablename__ = "analysis_results"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.analysis_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    data_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    null_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unique_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avg_value: Mapped[Optional[float]] = mapped_column(nullable=True)
    summary_stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnalysisInsight(ModelBase):
    __tablename__ = "analysis_insights"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.analysis_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    insight_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Dashboard(ModelBase):
    __tablename__ = "dashboards"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # grid | free
    layout: Mapped[str] = mapped_column(String(20), nullable=False, default="grid")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    css_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    js_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DashboardWidget(ModelBase):
    __tablename__ = "dashboard_widgets"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    dashboard_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )
    # chart | table | metric | text
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position_x: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position_y: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    width: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    height: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    analysis_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.analysis_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    chart_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ConversationMessage(ModelBase):
    __tablename__ = "conversation_messages"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    # user | assistant
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sql_generation_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_catalog.sql_generations.id", ondelete="SET NULL"),
        nullable=True,
    )
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
