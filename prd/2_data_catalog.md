# Data Catalog (Feature 2)

## Overview

Schema browsing and semantic discovery system that automatically generates vector-indexed metadata for connected data sources, and provides both structured browsing and natural-language search over that metadata.

This feature combines two concerns that share the same underlying data (`table_documents`):
- **Catalog generation**: introspect a data source → build `schemas`/`tables`/`columns` records → embed DDL content → store in `table_documents`.
- **Semantic search**: embed a natural-language query → cosine-search `table_documents` → return ranked results.

The frontend exposes both as tabs inside a single "Data Catalog" view:
- **Browse tab** — navigate schema tree, view column details.
- **Search tab** — natural-language vector similarity search.

## Infrastructure Context

- **PostgreSQL (pgvector)**: Stores catalog metadata (`schemas`, `tables`, `columns`) and vector embeddings (`table_documents`, HNSW index).
- **Temporal**: Orchestrates background schema synchronization (large catalogs take minutes to embed).
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, cosine similarity).

## Database Schema

```sql
-- Structured catalog metadata
CREATE TABLE schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    schema_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(data_source_id, schema_name)
);

CREATE TABLE tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id UUID NOT NULL REFERENCES schemas(id) ON DELETE CASCADE,
    table_name VARCHAR(255) NOT NULL,
    table_type VARCHAR(20) DEFAULT 'table' CHECK (table_type IN ('table', 'view')),
    row_count BIGINT DEFAULT 0,
    -- Pulled from COMMENT ON TABLE / pg_description on every sync. May be overwritten.
    source_description TEXT,
    -- Written by the user via the UI. Never overwritten by sync.
    user_description TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(schema_id, table_name)
);

CREATE TABLE columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id UUID NOT NULL REFERENCES tables(id) ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    is_nullable BOOLEAN DEFAULT TRUE,
    default_value TEXT,
    is_primary_key BOOLEAN DEFAULT FALSE,
    is_foreign_key BOOLEAN DEFAULT FALSE,
    references_column VARCHAR(255),
    -- Pulled from col_description / pg_description on every sync. May be overwritten.
    source_description TEXT,
    -- Written by the user via the UI. Never overwritten by sync.
    user_description TEXT,
    ordinal_position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(table_id, column_name)
);

-- Vector store for semantic search
CREATE TABLE table_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_id UUID REFERENCES tables(id) ON DELETE CASCADE,
    document_type VARCHAR(10) NOT NULL CHECK (document_type IN ('ddl', 'doc', 'example')),
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255),
    title VARCHAR(500),
    content TEXT NOT NULL,
    tags TEXT[],
    embedding VECTOR(384),  -- all-MiniLM-L6-v2
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_table_documents_embedding
    ON table_documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Search analytics
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    search_type VARCHAR(50),
    results_count INTEGER,
    search_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_tables_schema ON tables(schema_id, table_name);
CREATE INDEX idx_columns_table ON columns(table_id, column_name);
CREATE INDEX idx_tables_tags ON tables USING GIN(tags);
```

## API Endpoints

```
# Browse
GET    /api/v1/data-catalog/sources/{id}                    # Full catalog tree by data source
GET    /api/v1/data-catalog/schemas                         # Schema list
GET    /api/v1/data-catalog/tables                          # Table list (filterable)
GET    /api/v1/data-catalog/tables/{id}                     # Table detail with columns
GET    /api/v1/data-catalog/search                          # Keyword search (table/column names)
GET    /api/v1/data-catalog/stats                           # Catalog statistics
POST   /api/v1/data-catalog/refresh                         # Trigger catalog sync (Temporal workflow)
PATCH  /api/v1/data-catalog/tables/{id}/description         # Update user description for a table
PATCH  /api/v1/data-catalog/columns/{id}/description        # Update user description for a column

# Semantic search
POST   /api/v1/data-catalog/semantic-search     # Vector similarity search
POST   /api/v1/data-catalog/similar             # Find tables similar to a given table
GET    /api/v1/data-catalog/recommendations     # Table recommendations for a query
GET    /api/v1/data-catalog/history             # Search history
```

## Request/Response Models

### Browse — TableInfo
```python
{
  "id": "uuid",
  "schema_id": "uuid",
  "schema_name": "string",
  "table_name": "string",
  "table_type": "table|view",
  "row_count": "int",
  "source_description": "string",   # from COMMENT ON TABLE; overwritten on sync
  "user_description": "string",     # user-edited; never overwritten by sync
  "tags": ["string"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

Frontend display rule: show `user_description` if set, fall back to `source_description`.

### Browse — TableDetailResponse (extends TableInfo)
```python
{
  ...TableInfo,
  "columns": [
    {
      "id": "uuid",
      "column_name": "string",
      "data_type": "string",
      "is_nullable": "bool",
      "default_value": "string",
      "is_primary_key": "bool",
      "is_foreign_key": "bool",
      "references_column": "string",
      "source_description": "string",
      "user_description": "string",
      "ordinal_position": "int"
    }
  ]
}
```

### UpdateDescriptionRequest (PATCH table/column description)
```python
{
  "description": "string | null"   # null clears the user description
}
```

### Semantic Search — SemanticSearchRequest
```python
{
  "query": "string",
  "data_source_ids": ["uuid"],
  "search_type": "tables|columns|both",
  "limit": "int",
  "filters": {
    "schema_name": "string",
    "table_types": ["table", "view"]
  }
}
```

### Semantic Search — SemanticSearchResponse
```python
{
  "query": "string",
  "results": [
    {
      "type": "table|column",
      "table_id": "uuid",
      "schema_name": "string",
      "table_name": "string",
      "column_name": "string",
      "description": "string",
      "relevance_score": "float",
      "snippet": "string"
    }
  ],
  "total_found": "int",
  "search_time_ms": "int"
}
```

### CatalogStats
```python
{
  "total_schemas": "int",
  "total_tables": "int",
  "total_columns": "int",
  "data_sources": "int",
  "last_updated": "datetime"
}
```

## Implementation Details

### Description Ownership Model

Two separate fields on `tables` and `columns` prevent user annotations from being overwritten by catalog sync:

| Field | Written by | Overwritten on sync? |
|---|---|---|
| `source_description` | Introspection (`COMMENT ON TABLE/COLUMN`, `pg_description`) | Yes |
| `user_description` | `PATCH .../description` API | No |

Embedding content uses `user_description` when present, falls back to `source_description`.

### Catalog Refresh Flow

`POST /api/v1/data-catalog/refresh` triggers a Temporal workflow:

```
CatalogGenerationWorkflow.run(data_source_id):
  1. introspect_tables(data_source_id)
       # pulls schema, table, column metadata + COMMENT ON TABLE/COLUMN as source_description
  2. delete existing table_documents (derived — safe to rebuild)
  3. for each schema/table/column:
       upsert_schema(data_source_id, schema_name)
       upsert_table(schema_id, ..., source_description=...)   # user_description untouched
       upsert_column(table_id, ..., source_description=...)   # user_description untouched
       delete_stale_columns(table_id, active_names)
       delete_stale_tables(schema_id, active_names)
  4. delete_stale_schemas(data_source_id, active_names)
  5. for batch in chunks(tables, 16):
       content uses (user_description or source_description)
       vecs = embed_batch(contents)
       create_bulk(documents)             # document_type='ddl'
  6. return { schemas_synced, tables_synced, columns_synced }
```

**Why Temporal**: introspection of large schemas + embedding generation can take several minutes. The API returns `{ workflow_id, status: "RUNNING" }` immediately; the frontend polls `GET /refresh/status/{workflow_id}` for progress.

### Description Update + Re-embed Flow

`PATCH /api/v1/data-catalog/tables/{id}/description`:
1. Set `user_description` on the `tables` row.
2. Rebuild embedding content: `user_description or source_description`.
3. Re-embed the single `table_documents` row (`column_name IS NULL`).
4. Return updated `TableResponse`.

`PATCH /api/v1/data-catalog/columns/{id}/description`:
1. Set `user_description` on the `columns` row.
2. Rebuild embedding content for that column.
3. Re-embed the single `table_documents` row (`column_name = column.column_name`).
4. Return updated `ColumnResponse`.

### Document Content Generation

```python
def build_table_content(schema_name, table, columns):
    description = table.user_description or table.source_description or "No description"
    col_lines = "\n".join(
        f"  - {c.column_name} ({c.data_type})"
        f"{' PK' if c.is_primary_key else ''}"
        f"{' FK→' + c.references_column if c.is_foreign_key else ''}"
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
```

`user_description` takes priority over `source_description` for embeddings. This means richer user-written descriptions drive semantic search quality, while the raw source description is always preserved as a fallback.

One `table_documents` row per table (type=`ddl`) + one per column (type=`ddl`). Use `document_type` discriminator — do not create separate tables.

### Semantic Search Query

```python
stmt = (
    select(TableDocument)
    .where(TableDocument.document_type == "ddl")
    .order_by(TableDocument.embedding.cosine_distance(q_vec))
    .limit(k)
)
```

Similarity threshold: 0.3 minimum for search, 0.5 for similar-table queries.

### PostgreSQL Introspection

Uses `information_schema` queries (schemas, tables, columns, primary keys, foreign keys) plus `pg_class.reltuples` for fast approximate row counts. See `services/data_catalog.py → _introspect_postgres`.

## Integration Points

### With Data Source (Feature 1)
- Refresh is triggered manually or after a new data source is registered.
- Adapter credentials from `data_sources.config` (decrypted) are used for introspection.

### With Text-to-SQL (Feature 3)
- `SQLAgent` uses `retrieve_tables` skill → calls `POST /api/v1/data-catalog/semantic-search` with the user's question.
- `get_ddl` skill reads column details from `GET /api/v1/data-catalog/tables/{id}`.
- No embedding is called inside the agent — catalog already has pre-computed embeddings.

## Backend File Layout

```
controllers/data_catalog.py      — Browse + semantic search endpoints
services/data_catalog.py         — DataCatalogService (catalog refresh + semantic search methods)
repositories/data_catalog.py     — schemas/tables/columns CRUD
repositories/table_document.py   — cosine search on table_documents
repositories/search_history.py   — search_history inserts + queries
models/request/data_catalog.py   — CatalogRefreshRequest, SemanticSearchRequest, SimilarTableRequest
models/response/data_catalog.py  — TableResponse, SemanticSearchResponse, RecommendationResponse, ...
workflows/catalog.py             — CatalogGenerationWorkflow (Temporal)
activities/catalog.py            — introspect_tables, embed_batch, upsert_documents
```

`DataDiscoveryService` no longer exists — all logic lives in `DataCatalogService`.

## Security Considerations

- Data source credentials are decrypted only inside `_introspect_postgres` and never logged.
- `search_history` stores queries only (no user PII in current single-user setup).
- Vector embeddings expose table/column names — treat as internal metadata.
