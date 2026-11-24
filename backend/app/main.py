from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import logger
from app.middleware.request_id import RequestTimingMiddleware

# Enable Swagger UI and OpenAPI documentation in development only.
# In production, documentation endpoints are disabled to minimize the attack surface.
is_development = settings.DEBUG or settings.ENVIRONMENT.lower() != "production"

docs_url = "/docs" if is_development else None
redoc_url = "/redoc" if is_development else None
openapi_url = "/openapi.json" if is_development else None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    if is_development:
        logger.info("API documentation enabled at /docs, /redoc, and /openapi.json")
    else:
        logger.info("API documentation is disabled in production mode")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="DockScope: Monitor. Analyze. Control. Docker & Linux Infrastructure Intelligence Platform.",
    version=settings.APP_VERSION,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)

# CORS configuration - strict, non-permissive
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# Request ID and timing headers
app.add_middleware(RequestTimingMiddleware)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Aliases for API documentation in development
if is_development:
    @app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
    async def redirect_api_docs():
        return RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get(f"{settings.API_V1_STR}/redoc", include_in_schema=False)
    async def redirect_api_redoc():
        return RedirectResponse(url="/redoc", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
    async def redirect_api_openapi():
        return RedirectResponse(url="/openapi.json", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.APP_NAME,
        "tagline": settings.APP_TAGLINE,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if is_development else None,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )
