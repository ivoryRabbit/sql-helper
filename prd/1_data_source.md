# Data Source Management (Feature 1)

## Overview

Database connection management system supporting multiple database types with secure credential storage and connection pooling.

## Infrastructure Context

This feature is part of a comprehensive Text-to-SQL service infrastructure that includes:

- **PostgreSQL (pgvector)**: Primary database for storing data source configurations and credentials
- **Temporal**: Async workflow orchestration for data source synchronization tasks  
- **MinIO**: Object storage for export files and logs
- **Docker Compose**: Containerized deployment with all components

### Docker Components for Data Sources

```yaml
# Main PostgreSQL (Data Source Storage)
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
```

## Supported Database Types

- **PostgreSQL** - Primary relational database support
- **Amazon Redshift** - Cloud data warehouse support  
- **Trino** - Distributed query engine support

## API Endpoints

```
POST   /api/v1/data-sources              # Create data source
GET    /api/v1/data-sources              # List data sources
GET    /api/v1/data-sources/{id}         # Get specific data source
PUT    /api/v1/data-sources/{id}         # Update data source
DELETE /api/v1/data-sources/{id}         # Delete data source
POST   /api/v1/data-sources/{id}/test    # Test connection
POST   /api/v1/data-sources/{id}/sync    # Sync schema
```

## Request/Response Models

### DataSourceCreate
```python
{
  "name": "string",
  "type": "postgresql|redshift|trino", 
  "description": "string",
  "config": {
    // PostgreSQL specific
    "host": "string",
    "port": "int",
    "database": "string",
    "username": "string",
    "password": "string",  // encrypted at rest
    "ssl_mode": "string",
    
    // Redshift specific
    "cluster_id": "string",
    "region": "string",
    "iam_role": "string",
    
    // Trino specific
    "catalog": "string",
    "schema": "string",
    "coordinator_url": "string",
    
    // Common
    "connection_timeout": "int",
    "pool_size": "int",
    "max_overflow": "int"
  }
}
```

### DataSourceResponse
```python
{
  "id": "uuid",
  "name": "string",
  "type": "string",
  "description": "string", 
  "config": "object",  # password excluded
  "status": "connected|disconnected|error",
  "last_synced": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Database Schema

```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('postgresql', 'redshift', 'trino')),
    description TEXT,
    config JSONB NOT NULL,  -- encrypted sensitive fields
    status VARCHAR(20) DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected', 'error')),
    last_synced TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Connection Management

### Connection Pool Strategy
- **Per-database connection pools** for optimal resource management
- **Automatic failover** and connection health monitoring
- **Configurable pool sizes** based on database type and expected load
- **Connection timeout management** to prevent hanging connections

### Security Features
- **Encrypted credential storage** using AES-256-GCM
- **Password exclusion** from API responses
- **SSL/TLS support** for all database connections
- **Connection validation** before returning to pool

## Implementation Details

### PostgreSQL Connection
```python
async def create_postgres_pool(config: dict):
    return await asyncpg.create_pool(
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['username'],
        password=decrypt_password(config['password']),
        ssl=config.get('ssl_mode', 'prefer'),
        min_size=config.get('pool_size', 5),
        max_size=config.get('max_overflow', 20)
    )
```

### Redshift Connection
```python
async def create_redshift_pool(config: dict):
    return await asyncpg.create_pool(
        host=f"{config['cluster_id']}.{config['region']}.redshift.amazonaws.com",
        port=config.get('port', 5439),
        database=config['database'],
        user=config['username'],
        password=decrypt_password(config['password']),
        ssl='require'
    )
```

### Trino Connection
```python
async def create_trino_client(config: dict):
    return aiohttp.ClientSession(
        base_url=config['coordinator_url'],
        auth=aiohttp.BasicAuth(config['username'], decrypt_password(config['password'])),
        headers={'X-Trino-Catalog': config['catalog']}
    )
```

## Testing and Validation

### Connection Test Endpoint
- Validates connectivity without executing queries
- Tests authentication and authorization
- Returns connection metadata and capabilities
- Updates data source status accordingly

### Schema Synchronization
- Automatically discovers database schemas
- Extracts table and column metadata
- Updates data catalog with latest schema information
- Handles schema changes and migrations

## Error Handling

### Connection Errors
- **Timeout handling** for slow or unresponsive databases
- **Retry logic** with exponential backoff
- **Circuit breaker pattern** to prevent cascading failures
- **Graceful degradation** when databases are unavailable

### Validation Errors
- **Configuration validation** before connection attempts
- **Credential verification** with secure password checking
- **Network connectivity** validation
- **Permission verification** for database access

## Performance Considerations

### Connection Pooling
- **Optimal pool sizing** based on concurrent user expectations
- **Connection reuse** to minimize overhead
- **Health checks** to maintain pool quality
- **Pool monitoring** and alerting

### Caching Strategy
- **Connection metadata caching** for faster lookups
- **Schema information caching** to reduce database load
- **Status caching** to avoid unnecessary health checks
- **TTL-based cache invalidation**

## Monitoring and Observability

### Metrics to Track
- **Connection pool utilization** (active/idle connections)
- **Connection establishment time**
- **Query execution time** per data source
- **Error rates** by database type and error type
- **Schema sync duration** and success rates

### Health Check Endpoints
```
GET /api/v1/data-sources/{id}/health    # Data source health
GET /api/v1/data-sources/health          # All data sources health
```

## Security and Encryption Strategy

### Password and API Key Encryption

**Encryption Requirements**
- **AES-256-GCM** for sensitive data at rest
- **Key Management**: Use AWS KMS or HashiCorp Vault for production
- **Environment Variables**: Master encryption key from environment
- **Field-level Encryption**: Only encrypt sensitive fields, not entire JSON

```python
# Encryption Service Example
class EncryptionService:
    def __init__(self, master_key: str):
        self.cipher = AES.new(master_key, AES.MODE_GCM)
    
    def encrypt_password(self, password: str) -> str:
        nonce = os.urandom(12)
        ciphertext, tag = self.cipher.encrypt_and_digest(password.encode())
        return base64.b64encode(nonce + ciphertext + tag).decode()
    
    def decrypt_password(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted.encode())
        nonce, ciphertext, tag = data[:12], data[12:-16], data[-16:]
        cipher = AES.new(self.master_key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode()
```

**Database Schema for Encryption**
```sql
-- Encrypted fields in data_sources
ALTER TABLE data_sources ADD COLUMN config_encrypted JSONB;
-- Migrate existing data
UPDATE data_sources SET config_encrypted = encrypt_sensitive_fields(config);
-- Drop unencrypted config after migration
ALTER TABLE data_sources DROP COLUMN config;
ALTER TABLE data_sources RENAME COLUMN config_encrypted TO config;
```

## Senior Backend Engineering Concerns

### 1. Connection Pool Management
```python
# Per-database connection strategies
class ConnectionManager:
    def __init__(self):
        self.pools = {}  # data_source_id -> connection pool
    
    async def get_connection(self, data_source_id: UUID):
        if data_source_id not in self.pools:
            config = await self.get_data_source_config(data_source_id)
            self.pools[data_source_id] = self.create_pool(config)
        return self.pools[data_source_id].acquire()
    
    def create_pool(self, config):
        if config.type == 'postgresql':
            return asyncpg.create_pool(**config.connection_params)
        elif config.type == 'redshift':
            return asyncpg.create_pool(**config.redshift_params)
        elif config.type == 'trino':
            return aiohttp.ClientSession(**config.trino_params)
```

### 2. Scalability Considerations
- **Horizontal Scaling**: Stateless backend with Redis for session management
- **Database Sharding**: Consider by data_source_id for large deployments
- **Caching Strategy**: Multi-level caching (Redis + application)
- **Rate Limiting**: Per-user and per-data-source limits

### 3. Error Handling and Resilience
```python
# Circuit breaker pattern for external services
class DatabaseService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=DatabaseException
        )
    
    @circuit_breaker
    async def test_connection(self, data_source_config):
        # Implement retry logic with exponential backoff
        pass
```

## Security Best Practices

### Credential Management
- **Never log passwords** or sensitive configuration
- **Encrypt at rest** using strong encryption algorithms
- **Secure key management** for encryption keys
- **Regular credential rotation** policies

### Network Security
- **TLS encryption** for all database connections
- **VPN or private network** access when possible
- **IP whitelisting** for database access
- **Network segmentation** for different environments

## Integration Points

### With Data Catalog
- **Automatic schema discovery** feeds the catalog
- **Real-time updates** when schemas change
- **Metadata enrichment** with connection information

### With Text-to-SQL
- **Connection validation** before SQL generation
- **Dialect detection** for proper SQL syntax
- **Capability discovery** for supported features

### With Data Analysis
- **Query execution** through established connections
- **Result streaming** for large datasets
- **Resource management** for long-running queries
