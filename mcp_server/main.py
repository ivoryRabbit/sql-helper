from contextlib import asynccontextmanager

from fastapi import FastAPI

from clients import rag, trino
from configs import use_route_names_as_operation_ids, mount_mcp_server, register_routers


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    rag.init_client()
    trino.init_client()
    yield

    # Clear resources
    rag.close()
    trino.close()


app = FastAPI(lifespan=app_lifespan)
use_route_names_as_operation_ids(app)
register_routers(app)
mount_mcp_server(app)


if __name__ == "__main__":
    import uvicorn

    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
