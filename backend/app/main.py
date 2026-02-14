"""
Main FastAPI application with CORS and lifecycle management.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import settings
from .db import init_db, close_db
from .common.schemas import HealthResponse, ErrorResponse, StandardResponse
from .sports.football.router import router as football_router
from .sports.cricket.router import router as cricket_router
from .sports.rugby.router import router as rugby_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    logger.info("Starting Sports Dashboard API...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down Sports Dashboard API...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-sport analytics dashboard API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(football_router)
app.include_router(cricket_router)
app.include_router(rugby_router)


@app.get("/api/health", response_model=StandardResponse[HealthResponse])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    try:
        # Test database connection
        from .db import engine
        
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        health_data = HealthResponse(
            status="healthy",
            version=settings.app_version,
            database="connected"
        )
        
        return StandardResponse(
            data=health_data,
            message="Service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_data = HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            database="disconnected"
        )
        
        return StandardResponse(
            success=False,
            data=health_data,
            message="Service is unhealthy",
            errors={"database": str(e)}
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            error_code=str(exc.status_code)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="Internal server error",
            error_code="500",
            details={"type": type(exc).__name__}
        ).model_dump()
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Sports Dashboard API",
        "version": settings.app_version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )