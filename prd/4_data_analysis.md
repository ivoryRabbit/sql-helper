# Data Analysis (Feature 4)

## Overview

Query execution and analysis system that runs SQL queries, analyzes results, generates insights, and provides comprehensive data analysis with visualization suggestions.

## Infrastructure Context

This feature leverages core infrastructure for data processing:

- **PostgreSQL (pgvector)**: Stores analysis results, statistics, and insights
- **Temporal**: Orchestrates async SQL execution and analysis workflows
- **MinIO**: Object storage for export files and analysis artifacts
- **Connection Pooling**: Efficient database connection management for query execution

### Database Schema for Data Analysis

```sql
-- Data Analysis (Feature 4)
CREATE TABLE analysis_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sql_generation_id UUID REFERENCES sql_generations(id),
    executed_sql TEXT NOT NULL,
    execution_time_ms INTEGER,
    row_count INTEGER,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_executions(id) ON DELETE CASCADE,
    column_name VARCHAR(255),
    data_type VARCHAR(100),
    null_count INTEGER,
    unique_count INTEGER,
    min_value TEXT,
    max_value TEXT,
    avg_value NUMERIC,
    summary_stats JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analysis_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_executions(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    insight_text TEXT NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

```
POST   /api/v1/data-analysis/execute           # Execute SQL and analyze
POST   /api/v1/data-analysis/analyze            # Analyze result data
GET    /api/v1/data-analysis/results/{id}        # Get analysis results
GET    /api/v1/data-analysis/history            # Analysis history
POST   /api/v1/data-analysis/export             # Export results
```

## Request/Response Models

### AnalysisExecuteRequest
```python
{
  "sql": "string",
  "data_source_id": "uuid",
  "analysis_options": {
    "include_statistics": "bool",
    "generate_insights": "bool",
    "visualize_data": "bool",
    "limit_rows": "int"
  }
}
```

### AnalysisResult
```python
{
  "id": "uuid",
  "sql": "string",
  "execution_time_ms": "int",
  "row_count": "int",
  "columns": [
    {
      "name": "string",
      "type": "string",
      "null_count": "int",
      "unique_count": "int"
    }
  ],
  "data": "array",  # Actual data (with limit)
  "statistics": {
    "summary": "object",
    "insights": ["string"],
    "anomalies": ["string"]
  },
  "visualizations": [
    {
      "type": "chart|table",
      "config": "object",
      "data": "object"
    }
  ],
  "created_at": "datetime"
}
```

### DataExportRequest
```python
{
  "analysis_id": "uuid",
  "format": "csv|json|excel",
  "include_metadata": "bool"
}
```

## Database Schema

```sql
CREATE TABLE analysis_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sql_generation_id UUID REFERENCES sql_generations(id),
    executed_sql TEXT NOT NULL,
    execution_time_ms INTEGER,
    row_count INTEGER,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_executions(id) ON DELETE CASCADE,
    column_name VARCHAR(255),
    data_type VARCHAR(100),
    null_count INTEGER,
    unique_count INTEGER,
    min_value TEXT,
    max_value TEXT,
    avg_value NUMERIC,
    summary_stats JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analysis_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_executions(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    insight_text TEXT NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Query Execution

### Async Execution Framework
```python
async def execute_sql_analysis(request: AnalysisExecuteRequest, user_id: UUID):
    # Create analysis execution record
    execution_id = await create_execution_record(request, user_id)
    
    try:
        # Get database connection
        connection = await get_connection(request.data_source_id)
        
        # Start timing
        start_time = time.time()
        
        # Execute query
        if request.analysis_options.get('limit_rows'):
            sql_with_limit = f"SELECT * FROM ({request.sql}) AS subquery LIMIT {request.analysis_options['limit_rows']}"
        else:
            sql_with_limit = request.sql
        
        results = await connection.fetch(sql_with_limit)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Store execution results
        await store_execution_results(execution_id, results, execution_time_ms)
        
        # Trigger analysis workflow
        await trigger_analysis_workflow(execution_id, request.analysis_options)
        
        return {"execution_id": execution_id, "status": "completed"}
        
    except Exception as e:
        await mark_execution_failed(execution_id, str(e))
        raise
    finally:
        await connection.close()
```

### Query Optimization
```python
async def optimize_query(sql: str, data_source_id: UUID):
    # Analyze query plan
    plan = await get_execution_plan(sql, data_source_id)
    
    optimizations = []
    
    # Check for missing indexes
    if 'Seq Scan' in str(plan) and plan['Actual Rows'] > 1000:
        suggested_indexes = await suggest_indexes(sql, data_source_id)
        optimizations.extend(suggested_indexes)
    
    # Check for expensive operations
    if plan['Total Cost'] > 10000:
        optimizations.append("Consider adding WHERE clauses to reduce result set")
    
    # Check for JOIN optimization opportunities
    join_suggestions = await analyze_joins(sql, data_source_id)
    optimizations.extend(join_suggestions)
    
    return optimizations
```

## Statistical Analysis

### Descriptive Statistics
```python
async def calculate_column_statistics(column_data: List[Any], column_name: str, data_type: str):
    stats = {
        "column_name": column_name,
        "data_type": data_type,
        "null_count": column_data.count(None),
        "unique_count": len(set(filter(None, column_data))),
        "total_count": len(column_data)
    }
    
    # Remove null values for calculations
    non_null_data = [x for x in column_data if x is not None]
    
    if not non_null_data:
        return stats
    
    # Numeric statistics
    if data_type.lower() in ['integer', 'bigint', 'decimal', 'numeric', 'float', 'double']:
        numeric_data = [float(x) for x in non_null_data]
        stats.update({
            "min_value": min(numeric_data),
            "max_value": max(numeric_data),
            "mean_value": sum(numeric_data) / len(numeric_data),
            "median_value": median(numeric_data),
            "std_dev": stdev(numeric_data) if len(numeric_data) > 1 else 0,
            "quartiles": calculate_quartiles(numeric_data)
        })
    
    # Text statistics
    elif data_type.lower() in ['varchar', 'text', 'char']:
        text_data = [str(x) for x in non_null_data]
        stats.update({
            "min_length": min(len(x) for x in text_data),
            "max_length": max(len(x) for x in text_data),
            "avg_length": sum(len(x) for x in text_data) / len(text_data),
            "most_common": calculate_most_common(text_data)
        })
    
    # Date/time statistics
    elif 'date' in data_type.lower() or 'time' in data_type.lower():
        date_data = [parse_date(x) for x in non_null_data]
        date_data = [x for x in date_data if x is not None]
        if date_data:
            stats.update({
                "min_date": min(date_data),
                "max_date": max(date_data),
                "date_range_days": (max(date_data) - min(date_data)).days
            })
    
    return stats
```

### Correlation Analysis
```python
async def calculate_correlations(results: List[dict], numeric_columns: List[str]):
    correlations = {}
    
    for i, col1 in enumerate(numeric_columns):
        for col2 in numeric_columns[i+1:]:
            data1 = [float(row[col1]) for row in results if row[col1] is not None]
            data2 = [float(row[col2]) for row in results if row[col2] is not None]
            
            if len(data1) > 1 and len(data2) > 1:
                correlation = pearson_correlation(data1, data2)
                correlations[f"{col1}_vs_{col2}"] = {
                    "correlation": correlation,
                    "strength": interpret_correlation(correlation),
                    "sample_size": min(len(data1), len(data2))
                }
    
    return correlations
```

## Insight Generation

### Automated Insights
```python
async def generate_insights(execution_id: UUID, results: List[dict], statistics: dict):
    insights = []
    
    # Data quality insights
    quality_insights = await analyze_data_quality(results, statistics)
    insights.extend(quality_insights)
    
    # Pattern insights
    pattern_insights = await analyze_patterns(results, statistics)
    insights.extend(pattern_insights)
    
    # Outlier detection
    outlier_insights = await detect_outliers(results, statistics)
    insights.extend(outlier_insights)
    
    # Trend analysis (for time series data)
    trend_insights = await analyze_trends(results, statistics)
    insights.extend(trend_insights)
    
    # Store insights
    for insight in insights:
        await store_insight(execution_id, insight)
    
    return insights
```

### Data Quality Analysis
```python
async def analyze_data_quality(results: List[dict], statistics: dict):
    insights = []
    
    for column_stats in statistics['columns']:
        column_name = column_stats['column_name']
        
        # High null percentage
        null_percentage = (column_stats['null_count'] / column_stats['total_count']) * 100
        if null_percentage > 50:
            insights.append({
                "type": "data_quality",
                "text": f"Column '{column_name}' has {null_percentage:.1f}% null values",
                "severity": "high",
                "suggestion": "Consider data imputation or investigating missing data"
            })
        
        # Low cardinality for supposed high-cardinality columns
        if column_stats['data_type'] in ['varchar', 'text'] and column_stats['unique_count'] < 10:
            insights.append({
                "type": "data_quality",
                "text": f"Column '{column_name}' has low cardinality ({column_stats['unique_count']} unique values)",
                "severity": "medium",
                "suggestion": "Consider if this should be a categorical variable"
            })
    
    return insights
```

### Outlier Detection
```python
async def detect_outliers(results: List[dict], statistics: dict):
    insights = []
    
    for column_stats in statistics['columns']:
        if column_stats['data_type'].lower() in ['integer', 'bigint', 'decimal', 'numeric', 'float']:
            column_name = column_stats['column_name']
            data = [float(row[column_name]) for row in results if row[column_name] is not None]
            
            if len(data) > 10:  # Only for sufficient sample size
                outliers = detect_statistical_outliers(data)
                
                if outliers:
                    insights.append({
                        "type": "outlier",
                        "text": f"Column '{column_name}' has {len(outliers)} statistical outliers",
                        "severity": "medium",
                        "outlier_values": outliers[:5],  # Show first 5
                        "suggestion": "Review outliers for data quality issues"
                    })
    
    return insights
```

## Visualization Generation

### Chart Type Recommendation
```python
async def recommend_visualizations(results: List[dict], statistics: dict):
    visualizations = []
    
    numeric_columns = [col['column_name'] for col in statistics['columns'] 
                      if col['data_type'].lower() in ['integer', 'bigint', 'decimal', 'numeric', 'float']]
    
    categorical_columns = [col['column_name'] for col in statistics['columns'] 
                           if col['data_type'].lower() in ['varchar', 'text', 'char']]
    
    date_columns = [col['column_name'] for col in statistics['columns'] 
                    if 'date' in col['data_type'].lower() or 'time' in col['data_type'].lower()]
    
    # Time series visualization
    if date_columns and numeric_columns:
        for date_col in date_columns[:2]:  # Limit to 2 date columns
            for num_col in numeric_columns[:3]:  # Limit to 3 numeric columns
                visualizations.append({
                    "type": "line_chart",
                    "title": f"{num_col} over {date_col}",
                    "config": {
                        "x_axis": date_col,
                        "y_axis": num_col,
                        "aggregation": "sum" if len(results) > 100 else "none"
                    }
                })
    
    # Bar charts for categorical data
    if categorical_columns and numeric_columns:
        for cat_col in categorical_columns[:2]:
            for num_col in numeric_columns[:2]:
                visualizations.append({
                    "type": "bar_chart",
                    "title": f"{num_col} by {cat_col}",
                    "config": {
                        "x_axis": cat_col,
                        "y_axis": num_col,
                        "aggregation": "avg"
                    }
                })
    
    # Scatter plots for correlations
    if len(numeric_columns) >= 2:
        for i in range(min(3, len(numeric_columns) - 1)):
            visualizations.append({
                "type": "scatter_plot",
                "title": f"{numeric_columns[i]} vs {numeric_columns[i+1]}",
                "config": {
                    "x_axis": numeric_columns[i],
                    "y_axis": numeric_columns[i+1]
                }
            })
    
    return visualizations
```

### Chart Configuration Generation
```python
async def generate_chart_config(visualization: dict, results: List[dict]):
    chart_type = visualization['type']
    config = visualization['config']
    
    if chart_type == "line_chart":
        return {
            "type": "line",
            "data": {
                "labels": [row[config['x_axis']] for row in results],
                "datasets": [{
                    "label": config['y_axis'],
                    "data": [row[config['y_axis']] for row in results],
                    "borderColor": "rgb(75, 192, 192)",
                    "backgroundColor": "rgba(75, 192, 192, 0.2)"
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "x": {"title": {"display": True, "text": config['x_axis']}},
                    "y": {"title": {"display": True, "text": config['y_axis']}}
                }
            }
        }
    
    elif chart_type == "bar_chart":
        return {
            "type": "bar",
            "data": {
                "labels": list(set(row[config['x_axis']] for row in results)),
                "datasets": [{
                    "label": config['y_axis'],
                    "data": aggregate_by_category(results, config['x_axis'], config['y_axis']),
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgba(54, 162, 235, 1)"
                }]
            }
        }
    
    elif chart_type == "scatter_plot":
        return {
            "type": "scatter",
            "data": {
                "datasets": [{
                    "label": f"{config['x_axis']} vs {config['y_axis']}",
                    "data": [{"x": row[config['x_axis']], "y": row[config['y_axis']]} for row in results],
                    "backgroundColor": "rgba(255, 99, 132, 0.5)"
                }]
            }
        }
```

## Data Export

### Export Formats
```python
async def export_analysis_results(analysis_id: UUID, format: str, include_metadata: bool):
    analysis_results = await get_analysis_results(analysis_id)
    
    if format == "csv":
        return await export_to_csv(analysis_results, include_metadata)
    elif format == "json":
        return await export_to_json(analysis_results, include_metadata)
    elif format == "excel":
        return await export_to_excel(analysis_results, include_metadata)
    else:
        raise ValueError(f"Unsupported export format: {format}")

async def export_to_csv(results: dict, include_metadata: bool):
    import io
    import csv
    
    output = io.StringIO()
    
    if include_metadata:
        output.write("# Analysis Metadata\n")
        output.write(f"# Execution Time: {results['execution_time_ms']}ms\n")
        output.write(f"# Row Count: {results['row_count']}\n")
        output.write(f"# Created At: {results['created_at']}\n\n")
    
    writer = csv.DictWriter(output, fieldnames=[col['name'] for col in results['columns']])
    writer.writeheader()
    writer.writerows(results['data'])
    
    return output.getvalue()
```

## Performance Optimization

### Query Caching
```python
async def get_cached_analysis(sql_hash: str):
    cached = await redis.get(f"analysis:{sql_hash}")
    if cached:
        return json.loads(cached)
    return None

async def cache_analysis_results(sql_hash: str, results: dict, ttl: int = 3600):
    await redis.setex(f"analysis:{sql_hash}", ttl, json.dumps(results))
```

### Result Streaming
```python
async def stream_large_results(execution_id: UUID, chunk_size: int = 1000):
    connection = await get_connection_for_execution(execution_id)
    
    try:
        # Use server-side cursor for large results
        async with connection.transaction():
            cursor = await connection.cursor(execution_id)
            
            while True:
                chunk = await cursor.fetch(chunk_size)
                if not chunk:
                    break
                
                yield {
                    "type": "data_chunk",
                    "data": chunk,
                    "chunk_index": cursor.rowcount // chunk_size
                }
                
    finally:
        await connection.close()
```

### Senior Backend Engineering Concerns

#### 1. Query Execution Performance
- **Connection Pool Management**: Efficient connection reuse for multiple data sources
- **Query Optimization**: Automatic query plan analysis and optimization suggestions
- **Resource Management**: Memory and CPU monitoring for large queries
- **Timeout Handling**: Configurable timeouts for different query types

#### 2. Scalability Considerations
- **Async Processing**: Non-blocking query execution for concurrent analysis
- **Horizontal Scaling**: Stateless analysis service with distributed processing
- **Data Partitioning**: Consider by data_source_id for large deployments
- **Load Balancing**: Intelligent routing of analysis requests

#### 3. Data Quality and Validation
- **Result Validation**: Comprehensive data quality checks and anomaly detection
- **Statistical Analysis**: Automated insight generation with confidence scoring
- **Error Handling**: Graceful degradation for failed analyses
- **Audit Trail**: Complete logging of all analysis activities

#### 4. Export and Storage Optimization
- **MinIO Integration**: Efficient object storage for large result sets
- **Format Optimization**: Multiple export formats with compression
- **Retention Policies**: Automated cleanup of old analysis results
- **Access Control**: Secure sharing of analysis outputs

## Integration Points

### With Text-to-SQL
- **SQL validation** before execution
- **Performance analysis** of generated queries
- **Result interpretation** for user feedback
- **Query optimization** suggestions

### With Dashboard
- **Visualization data** for dashboard widgets
- **Analysis results** for dashboard content
- **Real-time updates** for live dashboards
- **Export functionality** for dashboard sharing

### With Data Catalog
- **Usage statistics** for table popularity
- **Query patterns** for catalog optimization
- **Performance metrics** for database tuning
- **Access patterns** for security analysis

## Monitoring and Analytics

### Performance Metrics
- **Query execution time** and success rates
- **Resource utilization** per analysis
- **Cache hit rates** for repeated queries
- **Export usage** and format preferences

### Quality Metrics
- **Data completeness** scores
- **Insight relevance** through user feedback
- **Visualization effectiveness** metrics
- **Error rates** and common issues

## Security Considerations

### Query Security
- **SQL injection prevention** through parameterization
- **Resource limits** to prevent abuse
- **Query timeout** enforcement
- **Access control** for sensitive data

### Data Privacy
- **Result filtering** based on permissions
- **Audit logging** for all analysis activities
- **Data retention policies** for analysis results
- **Export restrictions** for sensitive information
