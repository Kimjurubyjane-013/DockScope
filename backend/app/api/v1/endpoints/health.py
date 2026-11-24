from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.db.session import check_db_connectivity
from app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="Application Liveness Healthcheck")
async def get_health() -> HealthResponse:
    """
    Returns general application liveness health and version information.
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get("/ready", response_model=ReadyResponse, summary="PostgreSQL Database Readiness Check")
async def get_readiness() -> ReadyResponse:
    """
    Checks whether the application can connect to the underlying PostgreSQL database.
    Returns 200 when ready, 503 Service Unavailable if database is unreachable.
    """
    is_connected = await check_db_connectivity()
    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity check failed. PostgreSQL is unreachable.",
        )
    return ReadyResponse(
        status="ready",
        database="connected",
    )
