from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["root"])


@router.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse({"message": "SQL Helper API", "docs": "/docs"})
