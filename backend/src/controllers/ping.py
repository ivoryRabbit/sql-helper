from fastapi import APIRouter
from pydantic import BaseModel

from configs.container import container

router = APIRouter(prefix="/ping", tags=["health"])


class PingResponse(BaseModel):
    status: str
    database: str


@router.get("", response_model=PingResponse)
async def ping() -> PingResponse:
    db = container.database_manager()
    db_status = "ok" if db.is_available else "unavailable"
    return PingResponse(status="ok", database=db_status)
