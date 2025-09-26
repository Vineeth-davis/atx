# api/middleware.py
# Middleware for request tracing and logging

import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request IDs for tracing"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Add request ID to logger context
        logger.info(f"Request started: {request.method} {request.url.path}", extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'query_params': str(request.query_params),
            'client_ip': request.client.host if request.client else None,
        })
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log completion
            logger.info(f"Request completed: {response.status_code}", extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
            })
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(f"Request failed: {str(e)}", extra={
                'request_id': request_id,
                'duration_ms': duration_ms,
                'error': str(e),
            }, exc_info=True)
            
            raise

class QueryTracingMiddleware(BaseHTTPMiddleware):
    """Middleware to trace query executions"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only trace /ask endpoint
        if request.url.path == "/ask/" and request.method == "POST":
            # Generate trace ID for query
            trace_id = str(uuid.uuid4())
            request.state.trace_id = trace_id
            
            logger.info(f"Query trace started", extra={
                'request_id': getattr(request.state, 'request_id', None),
                'trace_id': trace_id,
                'endpoint': '/ask/',
            })
        
        response = await call_next(request)
        return response
