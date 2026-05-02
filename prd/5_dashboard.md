# Dashboard (Feature 5)

## Overview

Dashboard generation and management system that creates interactive HTML dashboards with customizable widgets, real-time data updates, and sharing capabilities.

## Infrastructure Context

This feature integrates with core infrastructure components:

- **PostgreSQL (pgvector)**: Stores dashboard configurations and widget metadata
- **MinIO**: Object storage for dashboard HTML files and static assets
- **WebSocket Infrastructure**: Real-time updates for live dashboards
- **Frontend Framework**: SvelteKit for interactive dashboard UI

### Database Schema for Dashboards

```sql
-- Dashboards (Feature 5)
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    layout VARCHAR(20) DEFAULT 'grid' CHECK (layout IN ('grid', 'free')),
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    html_content TEXT,
    css_content TEXT,
    js_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(50) NOT NULL CHECK (widget_type IN ('chart', 'table', 'metric', 'text')),
    title VARCHAR(255) NOT NULL,
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    width INTEGER DEFAULT 4,
    height INTEGER DEFAULT 3,
    analysis_id UUID REFERENCES analysis_executions(id),
    chart_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

```
POST   /api/v1/dashboards                     # Create dashboard
GET    /api/v1/dashboards                     # List dashboards
GET    /api/v1/dashboards/{id}                # Get specific dashboard
PUT    /api/v1/dashboards/{id}                # Update dashboard
DELETE /api/v1/dashboards/{id}                # Delete dashboard
POST   /api/v1/dashboards/{id}/widgets        # Add widget
PUT    /api/v1/dashboards/{id}/widgets/{widget_id}  # Update widget
DELETE /api/v1/dashboards/{id}/widgets/{widget_id} # Delete widget
GET    /api/v1/dashboards/{id}/html           # HTML rendering
POST   /api/v1/dashboards/{id}/share          # Create public link
```

## Request/Response Models

### DashboardCreate
```python
{
  "title": "string",
  "description": "string",
  "layout": "grid|free",
  "is_public": "bool",
  "tags": ["string"]
}
```

### DashboardResponse
```python
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "layout": "string",
  "widgets": [
    {
      "id": "uuid",
      "type": "chart|table|metric|text",
      "title": "string",
      "position": {"x": "int", "y": "int", "w": "int", "h": "int"},
      "config": "object",
      "data_source": "object"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### WidgetCreate
```python
{
  "type": "chart|table|metric|text",
  "title": "string",
  "analysis_id": "uuid",
  "chart_config": {
    "chart_type": "bar|line|pie|scatter",
    "x_axis": "string",
    "y_axis": "string",
    "group_by": "string"
  }
}
```

### DashboardHTML
```python
{
  "html": "string",
  "css": "string",
  "javascript": "string"
}
```

## Database Schema

```sql
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    layout VARCHAR(20) DEFAULT 'grid' CHECK (layout IN ('grid', 'free')),
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    html_content TEXT,
    css_content TEXT,
    js_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(50) NOT NULL CHECK (widget_type IN ('chart', 'table', 'metric', 'text')),
    title VARCHAR(255) NOT NULL,
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    width INTEGER DEFAULT 4,
    height INTEGER DEFAULT 3,
    analysis_id UUID REFERENCES analysis_executions(id),
    chart_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Dashboard Generation

### HTML Template System
```python
async def generate_dashboard_html(dashboard_id: UUID):
    dashboard = await get_dashboard(dashboard_id)
    widgets = await get_dashboard_widgets(dashboard_id)
    
    # Generate HTML structure
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/gridstack@6.0.1/dist/gridstack-all.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/gridstack@6.0.1/dist/gridstack.min.css" rel="stylesheet">
        <style>{css}</style>
    </head>
    <body>
        <div class="dashboard-container">
            <header class="dashboard-header">
                <h1>{title}</h1>
                <p>{description}</p>
                <div class="dashboard-controls">
                    <button id="refresh-btn">Refresh Data</button>
                    <button id="export-btn">Export</button>
                    <button id="fullscreen-btn">Fullscreen</button>
                </div>
            </header>
            <main class="dashboard-main">
                <div class="grid-stack">
                    {widgets}
                </div>
            </main>
        </div>
        <script>{javascript}</script>
    </body>
    </html>
    """
    
    # Generate widgets HTML
    widgets_html = ""
    for widget in widgets:
        widgets_html += await generate_widget_html(widget)
    
    # Generate CSS
    css_content = await generate_dashboard_css(dashboard, widgets)
    
    # Generate JavaScript
    js_content = await generate_dashboard_javascript(dashboard, widgets)
    
    return html_template.format(
        title=dashboard.title,
        description=dashboard.description,
        widgets=widgets_html,
        css=css_content,
        javascript=js_content
    )
```

### Widget Generation
```python
async def generate_widget_html(widget: dict):
    widget_html = f"""
    <div class="grid-stack-item" 
         gs-x="{widget['position_x']}" 
         gs-y="{widget['position_y']}" 
         gs-w="{widget['width']}" 
         gs-h="{widget['height']}"
         data-widget-id="{widget['id']}">
        <div class="grid-stack-item-content">
            <div class="widget-header">
                <h3>{widget['title']}</h3>
                <div class="widget-controls">
                    <button class="widget-refresh" data-widget-id="{widget['id']}">⟳</button>
                    <button class="widget-edit" data-widget-id="{widget['id']}">✎</button>
                    <button class="widget-delete" data-widget-id="{widget['id']}">×</button>
                </div>
            </div>
            <div class="widget-content" data-widget-type="{widget['widget_type']}">
                {await generate_widget_body(widget)}
            </div>
        </div>
    </div>
    """
    
    return widget_html

async def generate_widget_body(widget: dict):
    if widget['widget_type'] == 'chart':
        return f'<canvas id="chart-{widget["id"]}"></canvas>'
    elif widget['widget_type'] == 'table':
        return f'<div id="table-{widget["id"]}" class="data-table"></div>'
    elif widget['widget_type'] == 'metric':
        return f'<div id="metric-{widget["id"]}" class="metric-display"></div>'
    elif widget['widget_type'] == 'text':
        return f'<div id="text-{widget["id"]}" class="text-content">{widget.get("content", "")}</div>'
    return ''
```

## Widget Types

### Chart Widgets
```python
async def create_chart_widget(dashboard_id: UUID, widget_config: dict):
    # Validate chart configuration
    chart_config = widget_config['chart_config']
    analysis_id = widget_config['analysis_id']
    
    # Get analysis data
    analysis_data = await get_analysis_results(analysis_id)
    
    # Generate chart configuration
    chart_js = await generate_chart_javascript(analysis_data, chart_config)
    
    # Create widget record
    widget = await create_widget_record(
        dashboard_id=dashboard_id,
        widget_type='chart',
        title=widget_config['title'],
        analysis_id=analysis_id,
        chart_config=chart_config
    )
    
    return widget

async def generate_chart_javascript(analysis_data: dict, chart_config: dict):
    chart_type = chart_config['chart_type']
    x_axis = chart_config['x_axis']
    y_axis = chart_config['y_axis']
    
    return f"""
    const chartCtx = document.getElementById('chart-{analysis_data["id"]}').getContext('2d');
    new Chart(chartCtx, {{
        type: '{chart_type}',
        data: {{
            labels: {json.dumps([row[x_axis] for row in analysis_data['data']])},
            datasets: [{{
                label: '{y_axis}',
                data: {json.dumps([row[y_axis] for row in analysis_data['data']])},
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            scales: {{
                x: {{
                    title: {{
                        display: true,
                        text: '{x_axis}'
                    }}
                }},
                y: {{
                    title: {{
                        display: true,
                        text: '{y_axis}'
                    }}
                }}
            }}
        }}
    }});
    """
```

### Table Widgets
```python
async def create_table_widget(dashboard_id: UUID, widget_config: dict):
    analysis_id = widget_config['analysis_id']
    analysis_data = await get_analysis_results(analysis_id)
    
    # Generate table HTML
    table_html = await generate_table_html(analysis_data)
    
    widget = await create_widget_record(
        dashboard_id=dashboard_id,
        widget_type='table',
        title=widget_config['title'],
        analysis_id=analysis_id,
        chart_config=widget_config
    )
    
    return widget

async def generate_table_html(analysis_data: dict):
    columns = analysis_data['columns']
    data = analysis_data['data']
    
    # Generate table headers
    headers = "".join([f"<th>{col['name']}</th>" for col in columns])
    
    # Generate table rows
    rows = ""
    for row in data:
        cells = "".join([f"<td>{row.get(col['name'], '')}</td>" for col in columns])
        rows += f"<tr>{cells}</tr>"
    
    return f"""
    <table class="data-table">
        <thead><tr>{headers}</tr></thead>
        <tbody>{rows}</tbody>
    </table>
    """
```

### Metric Widgets
```python
async def create_metric_widget(dashboard_id: UUID, widget_config: dict):
    analysis_id = widget_config['analysis_id']
    analysis_data = await get_analysis_results(analysis_id)
    
    # Calculate metric value
    metric_config = widget_config['metric_config']
    metric_value = await calculate_metric(analysis_data, metric_config)
    
    widget = await create_widget_record(
        dashboard_id=dashboard_id,
        widget_type='metric',
        title=widget_config['title'],
        analysis_id=analysis_id,
        chart_config=metric_config
    )
    
    return widget

async def calculate_metric(analysis_data: dict, metric_config: dict):
    aggregation = metric_config.get('aggregation', 'sum')
    column = metric_config['column']
    
    values = [row[column] for row in analysis_data['data'] if row.get(column) is not None]
    
    if aggregation == 'sum':
        return sum(values)
    elif aggregation == 'avg':
        return sum(values) / len(values) if values else 0
    elif aggregation == 'count':
        return len(values)
    elif aggregation == 'max':
        return max(values) if values else 0
    elif aggregation == 'min':
        return min(values) if values else 0
    
    return 0
```

## Layout Management

### Grid Layout System
```python
async def generate_dashboard_css(dashboard: dict, widgets: list):
    css = """
    .dashboard-container {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #f5f5f5;
    }
    
    .dashboard-header {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .dashboard-header h1 {
        margin: 0 0 10px 0;
        color: #333;
    }
    
    .dashboard-controls {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }
    
    .dashboard-controls button {
        padding: 8px 16px;
        border: 1px solid #ddd;
        background: white;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .grid-stack-item-content {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    .widget-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px;
        border-bottom: 1px solid #eee;
        background: #fafafa;
    }
    
    .widget-header h3 {
        margin: 0;
        color: #333;
        font-size: 16px;
    }
    
    .widget-controls {
        display: flex;
        gap: 5px;
    }
    
    .widget-controls button {
        width: 24px;
        height: 24px;
        border: none;
        background: transparent;
        cursor: pointer;
        border-radius: 3px;
    }
    
    .widget-controls button:hover {
        background: #e0e0e0;
    }
    
    .widget-content {
        padding: 15px;
        height: calc(100% - 60px);
    }
    
    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    
    .data-table th,
    .data-table td {
        padding: 8px;
        text-align: left;
        border-bottom: 1px solid #eee;
    }
    
    .data-table th {
        background: #f8f9fa;
        font-weight: 600;
    }
    
    .metric-display {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-size: 48px;
        font-weight: bold;
        color: #2196F3;
    }
    
    .text-content {
        padding: 15px;
        line-height: 1.6;
    }
    """
    
    return css
```

### Responsive Design
```python
async def generate_responsive_layout(dashboard: dict):
    # Generate responsive breakpoints
    responsive_config = {
        "breakpoints": {
            "lg": 1200,
            "md": 996,
            "sm": 768,
            "xs": 480
        },
        "columns": {
            "lg": 12,
            "md": 10,
            "sm": 6,
            "xs": 4
        }
    }
    
    return responsive_config
```

## Real-time Updates

### WebSocket Integration
```python
async def setup_realtime_updates(dashboard_id: UUID):
    return f"""
    // WebSocket connection for real-time updates
    const ws = new WebSocket(`ws://localhost:8000/ws/dashboard/{dashboard_id}`);
    
    ws.onmessage = function(event) {{
        const data = JSON.parse(event.data);
        
        if (data.type === 'widget_update') {{
            updateWidget(data.widget_id, data.data);
        }} else if (data.type === 'dashboard_refresh') {{
            refreshDashboard();
        }}
    }};
    
    function updateWidget(widgetId, data) {{
        const widget = document.querySelector(`[data-widget-id="${{widgetId}}"]`);
        if (widget) {{
            const content = widget.querySelector('.widget-content');
            if (content) {{
                // Update widget based on type
                updateWidgetContent(content, data);
            }}
        }}
    }}
    
    function refreshDashboard() {{
        // Refresh all widgets
        document.querySelectorAll('[data-widget-id]').forEach(widget => {{
            const widgetId = widget.getAttribute('data-widget-id');
            refreshWidget(widgetId);
        }});
    }}
    """
```

### Auto-refresh Configuration
```python
async def configure_auto_refresh(dashboard: dict):
    refresh_config = dashboard.get('auto_refresh', {})
    
    return f"""
    // Auto-refresh configuration
    const autoRefreshEnabled = {refresh_config.get('enabled', False)};
    const refreshInterval = {refresh_config.get('interval', 300)}; // seconds
    
    let refreshTimer;
    
    function startAutoRefresh() {{
        if (autoRefreshEnabled) {{
            refreshTimer = setInterval(refreshDashboard, refreshInterval * 1000);
        }}
    }}
    
    function stopAutoRefresh() {{
        if (refreshTimer) {{
            clearInterval(refreshTimer);
        }}
    }}
    
    // Start auto-refresh on page load
    startAutoRefresh();
    
    // Handle visibility change to pause/resume refresh
    document.addEventListener('visibilitychange', function() {{
        if (document.hidden) {{
            stopAutoRefresh();
        }} else {{
            startAutoRefresh();
        }}
    }});
    """
```

## Export and Sharing

### Dashboard Export
```python
async def export_dashboard(dashboard_id: UUID, format: str):
    if format == "html":
        return await export_as_html(dashboard_id)
    elif format == "pdf":
        return await export_as_pdf(dashboard_id)
    elif format == "image":
        return await export_as_image(dashboard_id)
    else:
        raise ValueError(f"Unsupported export format: {format}")

async def export_as_html(dashboard_id: UUID):
    dashboard_html = await generate_dashboard_html(dashboard_id)
    
    # Create standalone HTML with embedded CSS and JS
    standalone_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Export</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/gridstack@6.0.1/dist/gridstack-all.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/gridstack@6.0.1/dist/gridstack.min.css" rel="stylesheet">
        <style>{dashboard_html['css']}</style>
    </head>
    <body>
        {dashboard_html['html']}
        <script>{dashboard_html['javascript']}</script>
    </body>
    </html>
    """
    
    return standalone_html
```

### Public Sharing
```python
async def create_public_link(dashboard_id: UUID, expires_in: int = None):
    # Generate unique share token
    share_token = generate_share_token()
    
    # Store share link with expiration
    await db.execute("""
        INSERT INTO dashboard_shares (dashboard_id, share_token, expires_at)
        VALUES ($1, $2, $3)
    """, dashboard_id, share_token, calculate_expiration(expires_in))
    
    return {
        "share_url": f"{BASE_URL}/shared/{share_token}",
        "expires_at": calculate_expiration(expires_in)
    }
```

## Performance Optimization

### Lazy Loading
```python
async def setup_lazy_loading():
    return """
    // Lazy loading for widgets
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const widgetId = entry.target.getAttribute('data-widget-id');
                loadWidgetData(widgetId);
                observer.unobserve(entry.target);
            }
        });
    });
    
    // Observe all widgets
    document.querySelectorAll('[data-widget-id]').forEach(widget => {
        observer.observe(widget);
    });
    
    function loadWidgetData(widgetId) {
        fetch(`/api/v1/dashboards/widgets/${widgetId}/data`)
            .then(response => response.json())
            .then(data => {
                updateWidget(widgetId, data);
            })
            .catch(error => {
                console.error('Error loading widget data:', error);
            });
    }
    """
```

### Caching Strategy
```python
async def cache_dashboard_data(dashboard_id: UUID, ttl: int = 300):
    # Cache widget data
    widgets = await get_dashboard_widgets(dashboard_id)
    
    for widget in widgets:
        if widget['analysis_id']:
            cache_key = f"widget_data:{widget['id']}"
            widget_data = await get_analysis_results(widget['analysis_id'])
            await redis.setex(cache_key, ttl, json.dumps(widget_data))
```

### Senior Backend Engineering Concerns

#### 1. Dashboard Performance Optimization
- **Widget Lazy Loading**: Load dashboard widgets on demand for faster initial load
- **Data Caching**: Multi-level caching for widget data and dashboard configurations
- **HTML Generation**: Efficient server-side rendering with template caching
- **Asset Optimization**: Minification and compression of CSS/JS resources

#### 2. Scalability Considerations
- **Horizontal Scaling**: Stateless dashboard service with distributed caching
- **Database Optimization**: Efficient queries for dashboard and widget data
- **MinIO Integration**: Scalable object storage for dashboard exports
- **WebSocket Scaling**: Efficient real-time updates for multiple concurrent users

#### 3. Real-time Updates Architecture
- **WebSocket Management**: Efficient connection pooling and message broadcasting
- **Change Detection**: Intelligent updates only when data actually changes
- **Conflict Resolution**: Handle concurrent dashboard modifications
- **Performance Monitoring**: Track real-time update latency and success rates

#### 4. Security and Access Control
- **Dashboard Permissions**: Role-based access control for view/edit operations
- **Public Sharing**: Secure token-based sharing with expiration
- **Data Filtering**: Ensure widgets respect user data access permissions
- **Export Security**: Secure handling of dashboard exports and sharing

## Integration Points

### With Data Analysis
- **Real-time data** from analysis results
- **Visualization suggestions** based on analysis
- **Widget configuration** from analysis metadata
- **Performance optimization** for large datasets

### With Text-to-SQL
- **Dynamic widgets** based on generated queries
- **Automatic updates** when queries change
- **Query execution** for dashboard data
- **Error handling** for failed queries

### With User Interface
- **Drag-and-drop** widget positioning
- **Interactive charts** with zoom and filter
- **Real-time collaboration** for shared dashboards
- **Mobile-responsive** design

## Security Considerations

### Access Control
- **Dashboard permissions** for view/edit access
- **Data filtering** based on user roles
- **Share link security** with expiration
- **Audit logging** for dashboard access

### Data Privacy
- **Sensitive data masking** in widgets
- **Export restrictions** for confidential data
- **Public sharing controls** with approval
- **Data retention** policies for shared dashboards
