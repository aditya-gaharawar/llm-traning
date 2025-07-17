#!/usr/bin/env python3
"""
LLM Trainer App - Main FastAPI Application

This module initializes and configures the FastAPI application for the LLM Trainer.
It sets up middleware, includes routers, configures WebSocket connections,
and handles application lifecycle events.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware.base import BaseHTTPMiddleware

from backend.api.router import api_router
from backend.core.auth import get_current_user
from backend.core.config import get_settings, settings
from backend.core.websocket import ConnectionManager
from backend.db.session import dispose_engine, init_db
from backend.utils import format_error, setup_logger

# Setup logger
logger = setup_logger("main", logging.INFO)

# WebSocket connection manager
ws_manager = ConnectionManager()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and measuring performance."""

    async def dispatch(self, request: Request, call_next):
        """Log request details and timing."""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"(ID: {request_id})"
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"(ID: {request_id}) - Status: {response.status_code} "
                f"- Time: {process_time:.3f}s"
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"(ID: {request_id}) - Error: {str(e)} "
                f"- Time: {process_time:.3f}s"
            )
            
            # Re-raise the exception
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, rate_limit_per_minute: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit_per_minute
        self.request_counts = {}
        self.reset_task = None

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if client_ip in self.request_counts and self.request_counts[client_ip] >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=format_error(
                    message="Too many requests",
                    status_code=429,
                    error_code="rate_limit_exceeded",
                ),
            )
        
        # Increment request count
        if client_ip in self.request_counts:
            self.request_counts[client_ip] += 1
        else:
            self.request_counts[client_ip] = 1
            
            # Start reset task if not already running
            if self.reset_task is None or self.reset_task.done():
                self.reset_task = asyncio.create_task(self._reset_counts())
        
        # Process the request
        return await call_next(request)
    
    async def _reset_counts(self):
        """Reset request counts after one minute."""
        await asyncio.sleep(60)
        self.request_counts = {}


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Create FastAPI app
    app = FastAPI(
        title=settings.api.title,
        description=settings.api.description,
        version=settings.api.version,
        docs_url=settings.api.docs_url,
        redoc_url=settings.api.redoc_url,
        openapi_url=settings.api.openapi_url,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add rate limiting middleware if enabled
    if settings.security.enable_rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            rate_limit_per_minute=settings.security.rate_limit_per_minute,
        )
    
    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error(
                message=exc.detail,
                status_code=exc.status_code,
            ),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """Handle validation errors."""
        return JSONResponse(
            status_code=422,
            content=format_error(
                message="Validation error",
                status_code=422,
                details={"errors": exc.errors()},
            ),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions."""
        logger.exception(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=format_error(
                message="Internal server error",
                status_code=500,
                error_code="internal_server_error",
            ),
        )
    
    # Include API router
    app.include_router(api_router, prefix=settings.api.prefix)
    
    # WebSocket endpoint
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket endpoint for real-time updates."""
        await ws_manager.connect(websocket, client_id)
        try:
            while True:
                data = await websocket.receive_text()
                await ws_manager.process_message(websocket, data, client_id)
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected: {client_id}")
            await ws_manager.disconnect(websocket, client_id)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await ws_manager.disconnect(websocket, client_id)
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize database and other resources on startup."""
        logger.info("Starting LLM Trainer application")
        await init_db()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        logger.info("Shutting down LLM Trainer application")
        await dispose_engine()
        await ws_manager.close_all()
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "version": settings.api.version}
    
    # Mount static files if in production
    if not settings.debug:
        try:
            app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")
            logger.info("Static files mounted successfully")
        except Exception as e:
            logger.warning(f"Failed to mount static files: {str(e)}")
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=settings.server.workers,
    )
