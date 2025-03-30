"""
Debug middleware for FastAPI application.
This middleware logs request and response details for debugging purposes.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class DebugMiddleware(BaseHTTPMiddleware):
    """
    Middleware for debugging FastAPI requests and responses.
    Logs detailed information about each request and response.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Log request details
        logger.debug(f"Request {request_id} started: {request.method} {request.url.path}")
        
        # Try to log request body if it exists
        try:
            body = await request.body()
            if body:
                logger.debug(f"Request {request_id} body: {body.decode()}")
        except Exception as e:
            logger.debug(f"Request {request_id} body could not be logged: {str(e)}")
        
        # Log request headers
        logger.debug(f"Request {request_id} headers: {request.headers}")
        
        # Process the request and measure time
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response details
            logger.debug(
                f"Request {request_id} completed: {response.status_code} in {process_time:.4f}s"
            )
            
            # Add custom headers for debugging
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            # Log exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Request {request_id} failed after {process_time:.4f}s with error: {str(e)}",
                exc_info=True
            )
            raise
