from fastapi import FastAPI

from controllers import dashboard, data_analysis, data_catalog, data_source, home, ping, sql_assistant

API_PREFIX = "/api/v1"


def register_routers(app: FastAPI) -> None:
    app.include_router(home.router)
    app.include_router(ping.router, prefix=API_PREFIX)
    app.include_router(data_source.router, prefix=API_PREFIX)
    app.include_router(data_catalog.router, prefix=API_PREFIX)
    app.include_router(sql_assistant.router, prefix=API_PREFIX)
    app.include_router(data_analysis.router, prefix=API_PREFIX)
    app.include_router(dashboard.router, prefix=API_PREFIX)
