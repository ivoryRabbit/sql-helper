import httpx
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP


def mount_mcp_server(app: FastAPI):
    mcp_server = FastApiMCP(
        app,
        name="text-to-sql",
        description="MCP server for Text-to-SQL",
        include_tags=["MCP"],
        http_client=httpx.AsyncClient(timeout=300),
    )
    mcp_server.mount(app)