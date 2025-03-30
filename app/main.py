from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
import os

from app.core.config import settings
from app.api.endpoints import router as api_router
from app.middleware.debug_middleware import DebugMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get("LOG_LEVEL") != "DEBUG" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Gateway for accessing large language models",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add debug middleware (only in debug mode)
if os.environ.get("LOG_LEVEL") == "DEBUG":
    app.add_middleware(DebugMiddleware)
    logger.info("Debug middleware enabled")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the application."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Add root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the DSP AI Gateway",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }

if __name__ == "__main__":
    # Run the application with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
