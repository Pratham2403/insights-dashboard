"""
Main FastAPI application for the Sprinklr Insights Dashboard.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import uvicorn
from app.config.settings import settings
from app.api.routes import router as api_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for the Sprinklr Insights Dashboard",
    version="0.1.0",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


# Add error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.
    
    Args:
        request: The request that caused the exception.
        exc: The exception.
        
    Returns:
        JSON response with error details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


# Add health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status.
    """
    return {"status": "ok"}


# Add root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    
    Returns:
        Welcome message.
    """
    return {
        "message": "Welcome to the Sprinklr Insights Dashboard API",
        "documentation": "/docs",
        "health": "/health",
    }


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
