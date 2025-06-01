"""
FastAPI application for MathTTS v3.

This module sets up the FastAPI application with all middleware,
routers, and configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.infrastructure.config import get_settings
from src.infrastructure.logging import get_logger, correlation_id, init_logger
from .routers import expression_router, pattern_router, voice_router, health_router, auth_router
from .middleware import RateLimitMiddleware, APIKeyMiddleware
from .dependencies import startup_event, shutdown_event
from .openapi_config import get_custom_openapi_schema, get_openapi_config


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MathTTS API")
    await startup_event()
    
    yield
    
    # Shutdown
    logger.info("Shutting down MathTTS API")
    await shutdown_event()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()
    
    # Initialize logging
    init_logger()
    
    # Get OpenAPI config
    openapi_config = get_openapi_config()
    
    # Create FastAPI app
    app = FastAPI(
        title=openapi_config["title"],
        version=openapi_config["version"],
        description=openapi_config["description"],
        contact=openapi_config["contact"],
        license_info=openapi_config["license"],
        servers=openapi_config["servers"],
        openapi_tags=openapi_config["tags"],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    if settings.api.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add custom middleware
    
    # Rate limiting
    if settings.api.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.api.rate_limit_requests
        )
    
    # API key authentication
    if settings.api.api_key_enabled:
        app.add_middleware(
            APIKeyMiddleware,
            api_keys=settings.api.api_keys
        )
    
    # Request ID middleware
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        """Add correlation ID to all requests."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id.set(request_id)
        
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        logger.api_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_host=request.client.host if request.client else None
        )
        
        return response
    
    # Exception handlers
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ):
        """Handle validation errors."""
        logger.warning(
            "Request validation failed",
            errors=exc.errors(),
            body=exc.body
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "request_id": correlation_id.get()
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "request_id": correlation_id.get()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ):
        """Handle unexpected exceptions."""
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "request_id": correlation_id.get()
            }
        )
    
    # Include routers
    app.include_router(
        auth_router,
        prefix="/api/v1",
        tags=["authentication"]
    )
    app.include_router(
        expression_router,
        prefix="/api/v1/expressions",
        tags=["expressions"]
    )
    app.include_router(
        pattern_router,
        prefix="/api/v1/patterns",
        tags=["patterns"]
    )
    app.include_router(
        voice_router,
        prefix="/api/v1/voices",
        tags=["voices"]
    )
    app.include_router(
        health_router,
        prefix="/api/v1/health",
        tags=["health"]
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
            "status": "operational"
        }
    
    # Set custom OpenAPI schema
    app.openapi = lambda: get_custom_openapi_schema(app)
    
    return app


# Create the app instance
app = create_application()