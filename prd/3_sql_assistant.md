# SQL Assistant (Feature 3)

## Overview

SQL generation and validation system using Large Language Models (LLMs) to convert natural language queries into executable SQL with streaming responses and comprehensive validation.

Supports two modes:
- **Stateless**: single-turn generation without a session (no `session_id`).
- **Conversational**: multi-turn chatbot mode via `ConversationSession` + `ConversationMessage`. Pass `session_id` in each `generate` request; prior messages are automatically included in the LLM context (last 10) and the new turn is persisted.

## Infrastructure Context

This feature integrates with core infrastructure components:

- **PostgreSQL (pgvector)**: Stores SQL generation history and validation results
- **Temporal**: Orchestrates async LLM processing and SQL execution workflows
- **OpenAI API**: Primary LLM provider for SQL generation
- **Streaming Infrastructure**: Real-time response streaming for better UX

### Database Schema for SQL Generation

```sql
-- Text-to-SQL Generation (Feature 3)
CREATE TABLE sql_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_query TEXT NOT NULL,
    data_source_id UUID REFERENCES data_sources(id),
    selected_tables UUID[] REFERENCES tables(id),
    generated_sql TEXT NOT NULL,
    explanation TEXT,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    llm_model VARCHAR(100),
    llm_tokens_used INTEGER,
    execution_plan JSONB,
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'valid', 'invalid')),
    validation_errors TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

```
# SQL Generation
POST   /api/v1/sql-assistant/generate          # Generate SQL (Streaming SSE)
POST   /api/v1/sql-assistant/validate          # Validate SQL syntax + security
POST   /api/v1/sql-assistant/explain           # Explain SQL in plain English
POST   /api/v1/sql-assistant/optimize          # SQL optimization suggestions
GET    /api/v1/sql-assistant/history           # Generation history (stateless)

# Conversation Sessions
POST   /api/v1/sql-assistant/sessions          # Create a new conversation session
GET    /api/v1/sql-assistant/sessions          # List all sessions (newest first)
GET    /api/v1/sql-assistant/sessions/{id}     # Session detail with full message history
DELETE /api/v1/sql-assistant/sessions/{id}     # Delete session and all its messages
```

## Request/Response Models

### GenerateRequest
```python
{
  "query": "string",                    # required
  "data_source_id": "uuid | null",
  "selected_tables": ["uuid"] | null,
  "session_id": "uuid | null",          # attach to a conversation session (optional)
  "options": {
    "include_explanation": true,        # default true
    "sql_dialect": "postgresql|mysql|sqlite"  # default "postgresql"
  }
}
```

### GenerateResponse — SSE stream
Each line: `data: <json>\n\n`

```python
# Intermediate chunk
{"type": "sql_chunk", "content": "string", "generation_id": "uuid"}

# Final event
{
  "type": "generation_complete",
  "generation_id": "uuid",
  "sql": "string | null",
  "explanation": "string | null",
  "confidence_score": "float | null",
  "validation": {
    "is_valid": "bool",
    "syntax_errors": ["string"],
    "security_issues": ["string"],
    "suggestions": ["string"]
  }
}

# Error event
{"type": "error", "message": "string", "generation_id": "uuid | null"}
```

### ValidateRequest / ValidateResponse
```python
# Request
{"sql": "string", "data_source_id": "uuid | null"}

# Response
{
  "sql": "string",
  "validation": {
    "is_valid": "bool",
    "syntax_errors": ["string"],
    "security_issues": ["string"],
    "suggestions": ["string"]
  }
}
```

### ExplainRequest / ExplainResponse
```python
# Request
{"sql": "string", "dialect": "postgresql|mysql|sqlite"}

# Response
{"sql": "string", "explanation": "string"}
```

### OptimizeRequest / OptimizeResponse
```python
# Request
{"sql": "string", "dialect": "postgresql|mysql|sqlite"}

# Response
{"sql": "string", "suggestions": ["string"], "optimized_sql": "string | null"}
```

### CreateSessionRequest / SessionResponse
```python
# Request
{"title": "string (default: 'New Conversation')", "data_source_id": "uuid | null"}

# Response
{"id": "uuid", "title": "string", "data_source_id": "uuid | null", "created_at": "datetime", "updated_at": "datetime"}
```

### SessionDetailResponse
```python
{
  "session": SessionResponse,
  "messages": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "role": "user | assistant",
      "content": "string",
      "sql_generation_id": "uuid | null",
      "extra_metadata": "object | null",
      "created_at": "datetime"
    }
  ]
}
```

## Database Schema

```sql
-- Conversation sessions (multi-turn chatbot context)
CREATE TABLE data_catalog.conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID REFERENCES data_catalog.data_sources(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual messages within a session
CREATE TABLE data_catalog.conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES data_catalog.conversation_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sql_generation_id UUID REFERENCES data_catalog.sql_generations(id) ON DELETE SET NULL,
    extra_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SQL generation records (linked to a session optionally)
CREATE TABLE data_catalog.sql_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES data_catalog.conversation_sessions(id) ON DELETE SET NULL,
    user_query TEXT NOT NULL,
    data_source_id UUID REFERENCES data_catalog.data_sources(id) ON DELETE SET NULL,
    selected_tables UUID[],
    generated_sql TEXT,
    explanation TEXT,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    llm_model VARCHAR(100),
    llm_tokens_used INTEGER,
    execution_plan JSONB,
    validation_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (validation_status IN ('pending', 'valid', 'invalid')),
    validation_errors TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Key invariants
- `session_id` on `generate` request is optional — omitting it produces a stateless one-off generation.
- When `session_id` is provided, `generate_sql_streaming` appends `user` + `assistant` messages automatically after streaming completes.
- `conversation_messages.session_id` has `ON DELETE CASCADE` — deleting a session removes all its messages.
- LLM context window uses the 10 most recent messages per session (`get_by_session(limit=10)`).

## LLM Integration

### Model Selection
- **Primary Model**: OpenAI GPT-4 for complex queries
- **Fallback Model**: GPT-3.5-Turbo for simple queries
- **Future Support**: Claude, Gemini, and local models
- **Model Routing**: Based on query complexity and user preferences

### Prompt Engineering
```python
def build_sql_generation_prompt(query: str, schema_context: str, options: dict):
    base_prompt = f"""
    You are an expert SQL query generator. Convert the following natural language query to SQL.
    
    User Query: {query}
    
    Database Schema:
    {schema_context}
    
    Requirements:
    - Generate valid SQL for {options.get('sql_dialect', 'postgresql')}
    - Use proper table and column names from the schema
    - Include appropriate JOINs when needed
    - Apply reasonable WHERE clauses for filtering
    - Consider performance implications
    """
    
    if options.get('include_explanation'):
        base_prompt += "\n- Provide a clear explanation of the generated SQL"
    
    if options.get('difficulty_level') == 'basic':
        base_prompt += "\n- Keep the query simple and straightforward"
    elif options.get('difficulty_level') == 'advanced':
        base_prompt += "\n- You can use advanced SQL features like window functions, CTEs, etc."
    
    return base_prompt
```

### Streaming Implementation
```python
async def generate_sql_streaming(request: SQLGenerationRequest):
    # Get schema context
    schema_context = await get_schema_context(request.selected_tables)
    
    # Build prompt
    prompt = build_sql_generation_prompt(request.query, schema_context, request.options)
    
    # Create generation record
    generation_id = await create_generation_record(request)
    
    try:
        # Stream LLM response
        async for chunk in llm_client.stream_completion(prompt):
            if chunk.choices:
                delta = chunk.choices[0].delta
                
                # Stream SQL content
                if delta.content:
                    yield {
                        "type": "sql_chunk",
                        "content": delta.content,
                        "generation_id": generation_id
                    }
        
        # Final validation and storage
        final_sql = await get_complete_generation(generation_id)
        validation_result = await validate_sql(final_sql, request.data_source_id)
        
        yield {
            "type": "generation_complete",
            "generation_id": generation_id,
            "validation": validation_result
        }
        
    except Exception as e:
        await mark_generation_failed(generation_id, str(e))
        yield {
            "type": "error",
            "message": str(e),
            "generation_id": generation_id
        }
```

## SQL Validation

### Syntax Validation
```python
async def validate_sql_syntax(sql: str, dialect: str):
    try:
        if dialect == 'postgresql':
            parser = PostgresParser()
        elif dialect == 'mysql':
            parser = MySQLParser()
        elif dialect == 'sqlite':
            parser = SQLiteParser()
        
        parsed = parser.parse(sql)
        return {"is_valid": True, "parsed_tree": parsed}
    
    except SQLSyntaxError as e:
        return {
            "is_valid": False,
            "error": str(e),
            "line": e.line,
            "column": e.column
        }
```

### Semantic Validation
```python
async def validate_sql_semantics(sql: str, data_source_id: UUID):
    # Check table and column existence
    tables_used = extract_tables_from_sql(sql)
    columns_used = extract_columns_from_sql(sql)
    
    validation_errors = []
    
    for table in tables_used:
        if not await table_exists(table, data_source_id):
            validation_errors.append(f"Table '{table}' does not exist")
    
    for column in columns_used:
        if not await column_exists(column.table, column.name, data_source_id):
            validation_errors.append(f"Column '{column.name}' does not exist in table '{column.table}'")
    
    return {
        "is_valid": len(validation_errors) == 0,
        "errors": validation_errors
    }
```

### Security Validation
```python
async def validate_sql_security(sql: str):
    security_issues = []
    
    # Check for dangerous operations
    dangerous_patterns = [
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'TRUNCATE\s+TABLE',
        r'UPDATE\s+.*\s+SET',
        r'INSERT\s+INTO',
        r'GRANT\s+',
        r'REVOKE\s+'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            security_issues.append(f"Potentially dangerous operation detected: {pattern}")
    
    # Check for SQL injection patterns
    injection_patterns = [
        r"'.*OR.*'.*='.*'",
        r'".*OR.*".*=".*"',
        r'1=1',
        r'1\s*=\s*1'
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            security_issues.append(f"Potential SQL injection pattern detected: {pattern}")
    
    return {
        "is_secure": len(security_issues) == 0,
        "security_issues": security_issues
    }
```

## Context Management

### Schema Context Generation
```python
async def get_schema_context(table_ids: List[UUID]):
    context_parts = []
    
    for table_id in table_ids:
        table_info = await get_table_info(table_id)
        
        # Table description
        context_parts.append(f"Table: {table_info.schema_name}.{table_info.table_name}")
        if table_info.description:
            context_parts.append(f"Description: {table_info.description}")
        
        # Column information
        context_parts.append("Columns:")
        for column in table_info.columns:
            context_parts.append(
                f"  - {column.column_name} ({column.column_type})"
                f"{' - Primary Key' if column.is_primary_key else ''}"
                f"{' - Foreign Key to ' + column.references_column if column.is_foreign_key else ''}"
            )
        
        # Relationships
        relationships = await get_table_relationships(table_id)
        if relationships:
            context_parts.append("Relationships:")
            for rel in relationships:
                context_parts.append(f"  - {rel.description}")
        
        context_parts.append("")  # Empty line between tables
    
    return "\n".join(context_parts)
```

### Query Enhancement
```python
async def enhance_query_with_context(query: str, data_source_id: UUID):
    # Extract entities from query
    entities = await extract_entities(query)
    
    # Find relevant tables
    relevant_tables = await find_relevant_tables(entities, data_source_id)
    
    # Get additional context
    context = {
        "similar_queries": await get_similar_queries(query),
        "table_suggestions": relevant_tables,
        "column_hints": await get_column_hints(entities, data_source_id)
    }
    
    return context
```

## Performance Optimization

### Query Plan Analysis
```python
async def analyze_execution_plan(sql: str, data_source_id: UUID):
    connection = await get_connection(data_source_id)
    
    try:
        # Get execution plan
        plan = await connection.fetchval(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")
        
        # Analyze plan for performance issues
        performance_issues = []
        
        if plan['Total Cost'] > 10000:
            performance_issues.append("High cost query - consider optimization")
        
        if 'Seq Scan' in str(plan):
            performance_issues.append("Sequential scan detected - consider adding indexes")
        
        if 'Hash Join' in str(plan) and plan['Actual Rows'] > 100000:
            performance_issues.append("Large hash join - consider query optimization")
        
        return {
            "plan": plan,
            "estimated_cost": plan['Total Cost'],
            "performance_issues": performance_issues,
            "suggestions": generate_optimization_suggestions(plan)
        }
    
    finally:
        await connection.close()
```

### Caching Strategy
- **Query result caching** for repeated queries
- **LLM response caching** to reduce API calls
- **Schema context caching** for faster generation
- **Validation result caching** for common SQL patterns

## Error Handling and Recovery

### Generation Errors
```python
class SQLGenerationError(Exception):
    def __init__(self, message: str, error_type: str, suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(message)

async def handle_generation_error(error: Exception, query: str):
    if isinstance(error, LLMTimeoutError):
        raise SQLGenerationError(
            "Query generation timed out - try simplifying your request",
            "timeout",
            ["Break down complex queries into simpler parts", "Try more specific questions"]
        )
    
    elif isinstance(error, LLMRateLimitError):
        raise SQLGenerationError(
            "Too many requests - please try again later",
            "rate_limit",
            ["Wait a few moments before trying again"]
        )
    
    elif isinstance(error, SQLSyntaxError):
        raise SQLGenerationError(
            f"Invalid SQL generated: {error}",
            "syntax",
            ["Try rephrasing your question", "Be more specific about tables and columns"]
        )
```

### Fallback Strategies
```python
async def fallback_generation(query: str, data_source_id: UUID):
    # Try with simpler prompt
    simple_prompt = f"Convert to SQL: {query}"
    result = await generate_with_fallback_model(simple_prompt)
    
    if result:
        return result
    
    # Try template-based generation
    template_result = await generate_from_template(query, data_source_id)
    if template_result:
        return template_result
    
    # Return helpful error message
    return {
        "sql": None,
        "error": "Unable to generate SQL for this query",
        "suggestions": [
            "Try using more specific table and column names",
            "Break down complex questions into simpler parts",
            "Check if the tables you're referencing exist"
        ]
    }
```

### Senior Backend Engineering Concerns

#### 1. LLM Integration Architecture
```python
# Circuit breaker pattern for external services
class LLMService:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            expected_exception=LLMException
        )
    
    @circuit_breaker
    async def generate_sql(self, query: str):
        # Implement retry logic with exponential backoff
        pass
```

#### 2. Scalability Considerations
- **LLM Provider Diversity**: Support multiple providers (OpenAI, Anthropic, local models)
- **Token Management**: Efficient token usage tracking and optimization
- **Rate Limiting**: Per-user and per-provider rate limiting
- **Cost Optimization**: Model selection based on query complexity

#### 3. Performance Optimization
- **Streaming Responses**: Real-time SQL generation for better UX
- **Response Caching**: Cache similar query responses
- **Batch Processing**: Process multiple requests efficiently
- **Connection Pooling**: Optimize LLM API connections

#### 4. Security and Validation
- **SQL Injection Prevention**: Comprehensive validation of generated SQL
- **Query Sanitization**: Remove dangerous operations
- **Access Control**: Ensure generated SQL respects user permissions
- **Audit Logging**: Track all SQL generation activities

## Integration Points

### With Data Discovery
- **Table recommendations** based on query analysis
- **Column suggestions** for better SQL generation
- **Context enhancement** using search results
- **Query intent understanding** for accurate results

### With Data Analysis
- **SQL validation** before execution
- **Performance analysis** for generated queries
- **Execution planning** for optimization
- **Result interpretation** for user feedback

### With User Interface
- **Real-time streaming** of SQL generation
- **Syntax highlighting** for generated SQL
- **Error messages** with helpful suggestions
- **Query history** for quick access

## Monitoring and Analytics

### Generation Metrics
- **Success rate** of SQL generation
- **Average generation time** per query
- **LLM token usage** and costs
- **Validation pass rate** for generated SQL

### Quality Metrics
- **User satisfaction** through feedback
- **Query accuracy** through execution results
- **Common error patterns** and resolutions
- **Performance impact** of generated queries

## Future Enhancements

### Advanced Features
- **Session title auto-generation** from first user query
- **Query templates** for common patterns
- **Auto-completion** during query typing
- **Voice-to-SQL** capabilities

### Model Improvements
- **Fine-tuned models** for specific domains
- **Local model hosting** for privacy
- **Model ensemble** for better accuracy
- **Custom model training** with user data
