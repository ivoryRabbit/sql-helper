from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse, PlainTextResponse

from models.response.health_check import HealthCheck


router = APIRouter(prefix="", tags=["Health Check"])


@router.get("/")
def root() -> RedirectResponse:
    return RedirectResponse("/docs")


@router.get("/ping")
def ping() -> PlainTextResponse:
    return PlainTextResponse("ok")


@router.get(
    "/health",
    response_description="Return HTTP status code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health_check() -> HealthCheck:
    return HealthCheck(status="OK")
