"""
Resume Doctor API - Main Application

Production-ready FastAPI application with:
- Origin validation middleware
- Tier-based rate limiting
- Structured logging
- CORS configuration
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
import time
import logging
import json
from datetime import datetime

from app.core.config import settings
from app.core.rate_limits import (
    get_rate_limit_key, 
    rate_limit_exceeded_handler,
    get_tier_from_request
)
from app.api.v1.endpoints import analyze

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter with tier-aware key function
limiter = Limiter(key_func=get_rate_limit_key)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if not settings.IS_PRODUCTION else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.IS_PRODUCTION else None,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS configuration from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict to needed methods
    allow_headers=["*"],
)


# Origin validation middleware (additional layer on top of CORS)
@app.middleware("http")
async def validate_origin(request: Request, call_next):
    """
    Validate request origin in production.
    Strictly blocks requests without proper Origin or API Key.
    """
    # Skip validation for health checks and preflight
    if request.url.path in ["/health", "/"] or request.method == "OPTIONS":
        return await call_next(request)
    
    # In production, strictly validate origin
    if settings.IS_PRODUCTION:
        origin = request.headers.get("origin") or request.headers.get("referer", "")
        api_key = request.headers.get("x-api-key")
        
        # 1. Check for API Key bypass (Server-to-Server)
        if api_key and api_key == settings.API_SECRET_KEY:
            return await call_next(request)
            
        # 2. If no API Key, MUST have valid Origin
        if not origin:
            logger.warning(f"Blocked headless request to {request.url.path} from {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied: Missing Origin header"}
            )
            
        # 3. Check if origin is allowed
        origin_valid = False
        for allowed in settings.allowed_origins_list:
            if origin.startswith(allowed):
                origin_valid = True
                break
        
        if not origin_valid:
            logger.warning(json.dumps({
                "event": "origin_blocked",
                "origin": origin,
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat()
            }))
            return JSONResponse(
                status_code=403,
                content={"error": "Origin not allowed"}
            )
    
    return await call_next(request)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing and tier info"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Only log API calls, not health checks
    if not request.url.path.startswith("/health"):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": f"{process_time:.3f}s",
            "client_ip": request.client.host if request.client else "unknown",
            "tier": get_tier_from_request(request),
            "user_id": request.headers.get("X-User-Id", "guest"),
        }
        logger.info(json.dumps(log_data))
    
    return response


# Include routers
app.include_router(analyze.router, prefix=f"{settings.API_V1_STR}/analyze", tags=["analyze"])


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Resume Doctor API is running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "health": "/health",
            "vitals": f"{settings.API_V1_STR}/analyze/vitals",
            "deep_scan": f"{settings.API_V1_STR}/analyze/deep-scan"
        }
    }


@app.get("/health")
async def health():
    """
    Enhanced health check endpoint.
    Used by Railway for deployment health monitoring.
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "status": "up",
        "service": "InfiniteResumeDoctor",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "memory": {
            "used_mb": round(memory_info.rss / 1024 / 1024, 1),
        },
        "config": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "cors_origins": len(settings.cors_origins_list),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

