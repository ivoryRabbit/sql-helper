# Infrastructure and Architecture

## Overview

Text-to-SQL service infrastructure supporting 6 core features with scalable, secure architecture.

## Docker Compose Infrastructure

### Required Components

```yaml
version: '3.8'

services:
  # Main PostgreSQL (Data Catalog Storage)
  postgres:
    image: pgvector/pgvector:0.8.1-pg17
    container_name: vectordb
    environment:
      POSTGRES_DB: vectordb
      POSTGRES_USER: sqlhelper
      POSTGRES_PASSWORD: sqlhelper
      TZ: Asia/Seoul
    ports:
      - "5432:5432"
    volumes:
      - ./docker/vectordb/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
      - ./docker/volumes/vectordb:/var/lib/postgresql/data
    healthcheck:
      test: [ "CMD", "pg_isready", "-U", "sqlhelper", "-d", "vectordb" ]
      start_period: 5s
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    networks:
      - sql-helper-network

  # Temporal (Async Workflow Orchestration)
  temporal:
    image: temporalio/auto-setup:latest
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - DB_HOST=postgres
      - DB_USER=sqlhelper
      - DB_PASSWORD=sqlhelper
      - DB_NAME=vectordb
      - DEFAULT_NAMESPACE=default
    ports:
      - "7233:7233"
    depends_on:
      - postgres
    networks:
      - sql-helper-network

  # Temporal UI
  temporal-ui:
    image: temporalio/ui:latest
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    ports:
      - "8088:8080"
    depends_on:
      - temporal
    networks:
      - sql-helper-network

  # MinIO (Object Storage for Dashboard HTML)
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    networks:
      - sql-helper-network

  # Backend Application
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sql-helper-backend
    environment:
      DATABASE_URL: postgresql+psycopg://sqlhelper:sqlhelper@postgres:5432/vectordb
      TEMPORAL_ADDRESS: temporal:7233
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      TZ: Asia/Seoul
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - temporal
      - minio
    volumes:
      - ./backend:/app
    networks:
      - sql-helper-network
    restart: unless-stopped

  # Frontend (SvelteKit)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: sql-helper-frontend
    environment:
      VITE_BACKEND_URL: http://localhost:8000/api/v1
      TZ: Asia/Seoul
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - sql-helper-network
    restart: unless-stopped

  # Optional: Trino (for future data source support)
  # trino:
  #   container_name: trino
  #   image: trinodb/trino:450
  #   ports:
  #     - "543:543"
  #   volumes:
  #     - ./docker/trino/etc:/etc/trino
  #     - ./docker/volumes/trino:/var/lib/trino/data
  #   healthcheck:
  #     test: [ "CMD", "curl", "--fail", "http://localhost:543/v1/status" ]
  #     interval: 10s
  #     retries: 3
  #     start_period: 5s
  #   restart: unless-stopped
  #   networks:
  #     - sql-helper-network

volumes:
  vectordb_data:
  minio_data:

networks:
  sql-helper-network:
    driver: bridge
```

### Infrastructure Component Roles

**PostgreSQL (pgvector)**
- Data catalog storage
- User data source information
- History and analysis results
- Vector embeddings storage (384 dimensions)
- Primary vector search capabilities

**Temporal**
- Async workflow orchestration
- Data catalog synchronization tasks
- Background SQL execution jobs
- Dashboard generation workflows
- Long-running LLM processing

**MinIO**
- Object storage for dashboard HTML files
- Static asset storage
- Export file storage (CSV, Excel, JSON)
- S3-compatible storage interface

**Temporal UI**
- Workflow monitoring and debugging
- Task execution history
- Performance metrics
- Error tracking and retry management


## Database Schema Overview

The database schema is distributed across feature-specific files:

- **Feature 1 (Data Source)**: `data_sources` table for connection management
- **Feature 2 (Data Catalog)**: `schemas`, `tables`, `columns` tables for metadata
- **Feature 3 (Data Discovery)**: `table_documents` table for vector search
- **Feature 3 (Text-to-SQL)**: `sql_generations` table for SQL generation history
- **Feature 4 (Data Analysis)**: `analysis_executions`, `analysis_results`, `analysis_insights` tables
- **Feature 5 (Dashboard)**: `dashboards`, `dashboard_widgets` tables for dashboard management

See individual feature files for detailed schema definitions.


## Core Technology Stack

- **Backend**: FastAPI + SQLAlchemy async + pgvector
- **Vector Search**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) via pgvector
- **Async Workflows**: Temporal
- **Object Storage**: MinIO (S3-compatible)
- **LLM**: OpenAI GPT-4 or local models
- **Frontend**: SvelteKit (target from current Svelte 4)

## Implementation Strategy

### Progressive Implementation Steps
1. **Data Source** - Basic connection management
2. **Data Catalog** - Schema analysis and pgvector integration
3. **Data Discovery** - Embedding-based search
4. **Text-to-SQL** - LLM integration and streaming responses
5. **Data Analysis** - Async SQL execution and analysis
6. **Dashboard** - HTML generation and widget system

### Security Considerations
- Data source password encryption
- SQL injection prevention
- API rate limiting
- Database access control
- Sensitive data masking
