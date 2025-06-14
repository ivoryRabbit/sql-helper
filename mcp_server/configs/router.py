from fastapi import FastAPI

from routers import ping, mcp, rag


def register_routers(app: FastAPI) -> None:
    app.include_router(ping.router)
    app.include_router(mcp.router)
    app.include_router(rag.router)
