"""
CineFusion Backend API - Comprehensive Production Version
A production-ready FastAPI application for movie search and recommendations.
Features: intelligent search, autocomplete, caching, rate limiting, monitoring, and security.
"""

from fastapi import FastAPI, HTTPException, Query, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
import os
import sys
import logging
import time
import json
import pandas as pd
from functools import lru_cache
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import asyncio
import uuid

# Import configuration and monitoring
from config import config, APP_CONFIG
from monitoring import performance_monitor, alert_manager

# Import custom logging system
from logger import (
    setup_logging,
    get_request_logger,
    get_performance_logger,
    get_error_logger,
    get_security_logger,
    log_request,
    log_response,
    log_error,
    log_performance_metric,
    log_security_event,
)

# Initialize comprehensive logging with environment-aware configuration
environment = "production" if not config.DEBUG else "development"
loggers = setup_logging(environment=environment)
logger = loggers["app"]
api_logger = get_request_logger()
perf_logger = get_performance_logger()
error_logger = get_error_logger()
security_logger = get_security_logger()

# Add the process directory to the path
process_dir = Path(__file__).parent / "process"
sys.path.append(str(process_dir))

# Global variables for data structures
avl_tree = None
trie = None
movies_df = None
startup_time = time.time()


# Enhanced cache implementation with TTL and size limits
class AdvancedCache:
    """Advanced caching system with TTL, size limits, and statistics"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with TTL check"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.access_times[key] = time.time()
                self.hits += 1
                performance_monitor.record_cache_hit(True)
                return data
            else:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]

        self.misses += 1
        performance_monitor.record_cache_hit(False)
        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache with size management"""
        # Remove expired entries first
        self._cleanup_expired()

        # If cache is full, remove LRU items
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[key] = (value, time.time())
        self.access_times[key] = time.time()

    def _cleanup_expired(self) -> None:
        """Remove expired cache entries"""
        now = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]

    def _evict_lru(self) -> None:
        """Evict least recently used items"""
        if not self.access_times:
            return

        # Remove 20% of cache when full
        num_to_remove = max(1, self.max_size // 5)
        sorted_keys = sorted(self.access_times.items(), key=lambda x: x[1])

        for key, _ in sorted_keys[:num_to_remove]:
            if key in self.cache:
                del self.cache[key]
            del self.access_times[key]
            self.evictions += 1

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "evictions": self.evictions,
            "ttl_seconds": self.ttl,
        }


# Initialize cache
cache = (
    AdvancedCache(config.CACHE_MAX_SIZE, config.CACHE_TTL_SECONDS)
    if config.ENABLE_CACHING
    else None
)


# Rate limiting with sliding window
class SlidingWindowRateLimiter:
    """Sliding window rate limiter with per-IP tracking"""

    def __init__(self, requests: int = 100, window_seconds: int = 60):
        self.requests = requests
        self.window = window_seconds
        self.clients = {}
        self.cleanup_interval = 60  # Cleanup every minute
        self.last_cleanup = time.time()

    def is_allowed(self, client_ip: str) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed and return rate limit info"""
        now = time.time()

        # Periodic cleanup
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = now

        if client_ip not in self.clients:
            self.clients[client_ip] = []

        # Remove old requests outside the window
        self.clients[client_ip] = [
            req_time
            for req_time in self.clients[client_ip]
            if now - req_time < self.window
        ]

        # Check rate limit
        current_requests = len(self.clients[client_ip])
        remaining = max(0, self.requests - current_requests)

        if current_requests >= self.requests:
            reset_time = int(now + self.window)
            return False, {
                "allowed": False,
                "remaining": 0,
                "reset": reset_time,
                "limit": self.requests,
            }

        # Add current request
        self.clients[client_ip].append(now)
        reset_time = int(now + self.window)

        return True, {
            "allowed": True,
            "remaining": remaining - 1,
            "reset": reset_time,
            "limit": self.requests,
        }

    def _cleanup_old_entries(self) -> None:
        """Remove old client entries to prevent memory leak"""
        now = time.time()
        clients_to_remove = []

        for client_ip, requests in self.clients.items():
            # Remove requests older than window
            recent_requests = [r for r in requests if now - r < self.window]
            if recent_requests:
                self.clients[client_ip] = recent_requests
            else:
                clients_to_remove.append(client_ip)

        for client_ip in clients_to_remove:
            del self.clients[client_ip]


rate_limiter = SlidingWindowRateLimiter(
    config.RATE_LIMIT_REQUESTS, config.RATE_LIMIT_WINDOW
)


# Enhanced Pydantic Models with comprehensive validation
class MovieModel(BaseModel):
    """Enhanced movie model with comprehensive validation"""

    title: str = Field(..., min_length=1, max_length=500, description="Movie title")
    year: Optional[int] = Field(None, ge=1880, le=2030, description="Release year")
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, description="IMDb rating")
    genre: Optional[str] = Field(None, max_length=200, description="Movie genre")
    director: Optional[str] = Field(None, max_length=200, description="Director name")
    duration: Optional[int] = Field(
        None, ge=1, le=1000, description="Duration in minutes"
    )
    budget: Optional[float] = Field(None, ge=0, description="Movie budget")
    actors: Optional[str] = Field(None, max_length=1000, description="Main actors")
    plot: Optional[str] = Field(None, max_length=2000, description="Movie plot")
    country: Optional[str] = Field(
        None, max_length=100, description="Country of origin"
    )
    language: Optional[str] = Field(
        None, max_length=100, description="Primary language"
    )
    awards: Optional[str] = Field(
        None, max_length=500, description="Awards and nominations"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        return v.strip() if v else ""

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v):
        return v.strip() if v else None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Dark Knight",
                "year": 2008,
                "rating": 9.0,
                "genre": "Action|Crime|Drama",
                "director": "Christopher Nolan",
                "duration": 152,
                "budget": 185000000.0,
                "actors": "Christian Bale, Heath Ledger, Aaron Eckhart",
            }
        }


class SearchResponse(BaseModel):
    """Enhanced search response model"""

    movies: List[MovieModel]
    total_count: int = Field(..., description="Total number of movies found")
    query: str = Field(..., description="Original search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    execution_time_ms: float = Field(
        ..., description="Search execution time in milliseconds"
    )
    cached: bool = Field(
        default=False, description="Whether result was served from cache"
    )
    pagination: Dict[str, Any] = Field(
        default_factory=dict, description="Pagination information"
    )


class SuggestionsResponse(BaseModel):
    """Enhanced suggestions response model"""

    suggestions: List[str]
    query: str = Field(..., description="Original query")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    cached: bool = Field(
        default=False, description="Whether result was served from cache"
    )
    total_available: int = Field(default=0, description="Total suggestions available")


class HealthResponse(BaseModel):
    """Comprehensive health check response model"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    database_status: str = Field(..., description="Database connection status")
    movies_loaded: int = Field(..., description="Number of movies in database")
    cache_stats: Optional[Dict[str, Any]] = Field(None, description="Cache statistics")
    performance_metrics: Optional[Dict[str, Any]] = Field(
        None, description="Performance metrics"
    )
    system_info: Optional[Dict[str, Any]] = Field(
        None, description="System information"
    )


class ErrorResponse(BaseModel):
    """Standardized error response model"""

    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code")
    error_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique error ID"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp",
    )
    path: Optional[str] = Field(None, description="Request path where error occurred")


class StatsResponse(BaseModel):
    """Database and system statistics response"""

    database: Dict[str, Any]
    performance: Dict[str, Any]
    cache: Optional[Dict[str, Any]] = None
    system: Dict[str, Any]


# Async context manager for application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    global avl_tree, trie, movies_df

    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")

    # Initialize data structures
    try:
        # Import and initialize components
        from trie import Trie
        from avl import AVLTree

        # Change to process directory
        original_cwd = os.getcwd()
        os.chdir(str(process_dir))

        logger.info("Loading movie database...")
        movies_df = pd.read_csv(config.MOVIE_CSV_PATH, encoding=config.DB_ENCODING)
        logger.info(f"Loaded {len(movies_df)} movies from CSV")

        # Initialize AVL Tree
        logger.info("Initializing AVL Tree...")
        avl_tree = AVLTree()
        for title in movies_df["movie_title"].dropna():
            clean_title = title.strip()
            if clean_title:
                avl_tree.insert(clean_title)
        logger.info("AVL Tree initialized successfully")

        # Initialize Trie
        logger.info("Initializing Autocomplete Trie...")
        trie = Trie()
        movie_titles = [
            title.strip()
            for title in movies_df["movie_title"].dropna()
            if title.strip()
        ]
        trie.formTrie(movie_titles)
        logger.info("Trie initialized successfully")

        # Restore original working directory
        os.chdir(original_cwd)

        logger.info("Backend initialization complete")

        # Start background tasks
        if config.ENABLE_CACHING and cache:
            asyncio.create_task(periodic_cache_cleanup())

        asyncio.create_task(periodic_health_check())

    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        logger.warning("Using fallback movie data")

    yield

    # Cleanup
    logger.info("Shutting down CineFusion backend")


# Background tasks
async def periodic_cache_cleanup():
    """Periodic cache cleanup task"""
    while True:
        await asyncio.sleep(config.CACHE_CLEANUP_INTERVAL)
        if cache:
            cache._cleanup_expired()
            logger.debug(f"Cache cleanup completed. Current size: {len(cache.cache)}")


async def periodic_health_check():
    """Periodic health monitoring task"""
    while True:
        await asyncio.sleep(config.HEALTH_CHECK_INTERVAL)
        try:
            # Check for alerts
            alerts = alert_manager.check_alerts()
            if alerts:
                logger.warning(f"System alerts detected: {len(alerts)} issues")
        except Exception as e:
            logger.error(f"Health check failed: {e}")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title=config.API_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    lifespan=lifespan,
    docs_url=config.DOCS_URL if config.DEBUG else None,
    redoc_url=config.REDOC_URL if config.DEBUG else None,
    openapi_url=config.OPENAPI_URL if config.DEBUG else None,
    responses={
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)

# Add security middleware
if not config.DEBUG and config.TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.TRUSTED_HOSTS)

# CORS middleware with enhanced configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
    max_age=config.CORS_MAX_AGE,
)


# Enhanced middleware for monitoring, rate limiting, and comprehensive logging
@app.middleware("http")
async def comprehensive_middleware(request: Request, call_next):
    """Comprehensive middleware for rate limiting, monitoring, error handling, and logging"""
    start_time = time.time()
    client_ip = request.client.host
    request_id = str(uuid.uuid4())
    user_agent = request.headers.get("user-agent", "unknown")

    # Log incoming request
    log_request(
        request_id=request_id,
        method=request.method,
        endpoint=str(request.url.path),
        user_ip=client_ip,
        user_agent=user_agent,
        query_params=dict(request.query_params) if request.query_params else None,
    )

    # Rate limiting with security logging
    allowed, rate_info = rate_limiter.is_allowed(client_ip)
    if not allowed:
        log_security_event(
            event_type="rate_limit_exceeded",
            severity="warning",
            user_ip=client_ip,
            user_agent=user_agent,
            details={"endpoint": str(request.url.path), "limit": rate_info},
        )

        response = JSONResponse(
            status_code=429,
            content=ErrorResponse(
                detail=config.ERROR_MESSAGES["rate_limit_exceeded"],
                error_code="RATE_LIMIT_EXCEEDED",
                path=str(request.url.path),
            ).dict(),
        )
        response.headers[config.RESPONSE_HEADERS["rate_limit_remaining"]] = str(
            rate_info["remaining"]
        )
        response.headers[config.RESPONSE_HEADERS["rate_limit_reset"]] = str(
            rate_info["reset"]
        )

        # Log response
        process_time = (time.time() - start_time) * 1000
        log_response(request_id, str(request.url.path), 429, process_time)
        return response

    # Process request
    try:
        response = await call_next(request)
        error_occurred = response.status_code >= 400

        # Log errors
        if error_occurred:
            log_security_event(
                event_type="http_error",
                severity="warning" if response.status_code < 500 else "error",
                user_ip=client_ip,
                details={
                    "status_code": response.status_code,
                    "endpoint": str(request.url.path),
                    "method": request.method,
                },
            )

    except Exception as e:
        error_occurred = True

        # Log error with full context
        log_error(
            error=e,
            request_id=request_id,
            endpoint=str(request.url.path),
            user_ip=client_ip,
            additional_context={
                "method": request.method,
                "user_agent": user_agent,
                "query_params": (
                    dict(request.query_params) if request.query_params else None
                ),
            },
        )

        response = JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=config.ERROR_MESSAGES["internal_error"],
                error_code="INTERNAL_ERROR",
                error_id=request_id,
                path=str(request.url.path),
            ).dict(),
        )

    # Add timing and monitoring
    process_time = (time.time() - start_time) * 1000
    performance_monitor.record_request(process_time, error_occurred)

    # Log performance metrics
    log_performance_metric(
        metric_name="request_duration",
        value=process_time,
        unit="ms",
        endpoint=str(request.url.path),
        additional_data={
            "method": request.method,
            "status_code": response.status_code,
            "error_occurred": error_occurred,
        },
    )

    # Add response headers
    response.headers[config.RESPONSE_HEADERS["process_time"]] = str(process_time / 1000)
    response.headers[config.RESPONSE_HEADERS["rate_limit_remaining"]] = str(
        rate_info["remaining"]
    )
    response.headers["X-Request-ID"] = request_id

    # Log response
    response_size = None
    if hasattr(response, "body") and response.body:
        response_size = len(response.body)

    log_response(
        request_id=request_id,
        endpoint=str(request.url.path),
        status_code=response.status_code,
        response_time=process_time,
        response_size=response_size,
    )

    return response


# Error handlers with enhanced logging
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized error response and logging"""
    client_ip = request.client.host

    # Log HTTP exception
    log_error(
        error=exc,
        endpoint=str(request.url.path),
        user_ip=client_ip,
        additional_context={
            "status_code": exc.status_code,
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            path=str(request.url.path),
        ).dict(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with comprehensive error tracking and logging"""
    client_ip = request.client.host
    request_id = str(uuid.uuid4())

    # Log critical error
    log_error(
        error=exc,
        request_id=request_id,
        endpoint=str(request.url.path),
        user_ip=client_ip,
        additional_context={
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "query_params": (
                dict(request.query_params) if request.query_params else None
            ),
        },
    )

    # Log security event for unexpected errors
    log_security_event(
        event_type="unexpected_error",
        severity="critical",
        user_ip=client_ip,
        details={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "endpoint": str(request.url.path),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail=config.ERROR_MESSAGES["internal_error"],
            error_code="INTERNAL_ERROR",
            error_id=request_id,
            path=str(request.url.path),
        ).dict(),
    )
    error_id = str(uuid.uuid4())
    logger.error(f"Global exception {error_id}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail=config.ERROR_MESSAGES["internal_error"],
            error_code="INTERNAL_ERROR",
            error_id=error_id,
            path=str(request.url.path),
        ).dict(),
    )


# Helper functions
def movie_to_dict(row) -> Dict[str, Any]:
    """Convert DataFrame row to MovieModel dict with comprehensive mapping"""
    return {
        "title": str(row.get("movie_title", "")).strip(),
        "year": (
            int(row.get("title_year", 0)) if pd.notna(row.get("title_year")) else None
        ),
        "rating": (
            float(row.get("imdb_score", 0)) if pd.notna(row.get("imdb_score")) else None
        ),
        "genre": (
            str(row.get("genres", "")).strip() if pd.notna(row.get("genres")) else None
        ),
        "director": (
            str(row.get("director_name", "")).strip()
            if pd.notna(row.get("director_name"))
            else None
        ),
        "duration": (
            int(row.get("duration", 0)) if pd.notna(row.get("duration")) else None
        ),
        "budget": float(row.get("budget", 0)) if pd.notna(row.get("budget")) else None,
        "actors": (
            str(row.get("actor_1_name", "")).strip()
            if pd.notna(row.get("actor_1_name"))
            else None
        ),
        "plot": (
            str(row.get("plot_keywords", "")).strip()
            if pd.notna(row.get("plot_keywords"))
            else None
        ),
        "country": (
            str(row.get("country", "")).strip()
            if pd.notna(row.get("country"))
            else None
        ),
        "language": (
            str(row.get("language", "")).strip()
            if pd.notna(row.get("language"))
            else None
        ),
        "awards": None,  # Not in current dataset
    }


def search_movies_in_df(
    query: str,
    limit: int = 10,
    offset: int = 0,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    director: Optional[str] = None,
    actor: Optional[str] = None,
    sort_by: str = "rating",
    sort_order: str = "desc",
) -> tuple[List[MovieModel], int, Dict[str, Any]]:
    """Enhanced movie search with comprehensive filtering and sorting"""
    if movies_df is None:
        return [], 0, {}

    # Start with all movies
    filtered_df = movies_df.copy()
    filters_applied = {}

    # Apply search query
    if query:
        query_lower = query.lower()
        title_match = (
            filtered_df["movie_title"]
            .str.lower()
            .str.contains(query_lower, na=False, regex=False)
        )
        director_match = (
            filtered_df["director_name"]
            .str.lower()
            .str.contains(query_lower, na=False, regex=False)
        )
        actor_match = (
            filtered_df["actor_1_name"]
            .str.lower()
            .str.contains(query_lower, na=False, regex=False)
        )
        genre_match = (
            filtered_df["genres"]
            .str.lower()
            .str.contains(query_lower, na=False, regex=False)
        )

        filtered_df = filtered_df[
            title_match | director_match | actor_match | genre_match
        ]
        filters_applied["query"] = query

    # Apply filters
    if genre:
        filtered_df = filtered_df[
            filtered_df["genres"].str.contains(genre, case=False, na=False, regex=False)
        ]
        filters_applied["genre"] = genre

    if year:
        filtered_df = filtered_df[filtered_df["title_year"] == year]
        filters_applied["year"] = year

    if min_rating:
        filtered_df = filtered_df[filtered_df["imdb_score"] >= min_rating]
        filters_applied["min_rating"] = min_rating

    if max_rating:
        filtered_df = filtered_df[filtered_df["imdb_score"] <= max_rating]
        filters_applied["max_rating"] = max_rating

    if director:
        filtered_df = filtered_df[
            filtered_df["director_name"].str.contains(
                director, case=False, na=False, regex=False
            )
        ]
        filters_applied["director"] = director

    if actor:
        filtered_df = filtered_df[
            filtered_df["actor_1_name"].str.contains(
                actor, case=False, na=False, regex=False
            )
        ]
        filters_applied["actor"] = actor

    # Sort results
    sort_column_mapping = {
        "rating": "imdb_score",
        "year": "title_year",
        "title": "movie_title",
        "duration": "duration",
        "budget": "budget",
    }

    if sort_by in sort_column_mapping:
        sort_column = sort_column_mapping[sort_by]
        ascending = sort_order.lower() == "asc"
        filtered_df = filtered_df.sort_values(
            sort_column, ascending=ascending, na_position="last"
        )
        filters_applied["sort_by"] = sort_by
        filters_applied["sort_order"] = sort_order

    # Get total count before pagination
    total_count = len(filtered_df)

    # Apply pagination
    paginated_df = filtered_df.iloc[offset : offset + limit]

    # Convert to MovieModel list
    movies = []
    for _, row in paginated_df.iterrows():
        try:
            movie_dict = movie_to_dict(row)
            movies.append(MovieModel(**movie_dict))
        except Exception as e:
            logger.warning(f"Failed to create movie model: {e}")
            continue

    return movies, total_count, filters_applied


def get_fallback_movies(limit: int = 5) -> List[MovieModel]:
    """Get fallback movies from configuration"""
    fallback_data = config.FALLBACK_MOVIES[:limit]
    return [MovieModel(**movie) for movie in fallback_data]


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with comprehensive health check"""
    uptime = time.time() - startup_time
    cache_stats = cache.get_stats() if cache else None
    performance_stats = performance_monitor.get_performance_summary()

    try:
        import psutil

        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": (
                psutil.disk_usage("/").percent
                if os.name != "nt"
                else psutil.disk_usage("C:\\").percent
            ),
        }
    except ImportError:
        system_info = {"status": "psutil not available"}

    return HealthResponse(
        status="healthy",
        version=config.APP_VERSION,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=uptime,
        database_status="connected" if movies_df is not None else "disconnected",
        movies_loaded=len(movies_df) if movies_df is not None else 0,
        cache_stats=cache_stats,
        performance_metrics=performance_stats,
        system_info=system_info,
    )


@app.get(f"{config.API_PREFIX}/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint with full system status"""
    return await root()


@app.get(f"{config.API_PREFIX}/search", response_model=SearchResponse)
async def search_movies(
    q: str = Query(
        ...,
        min_length=config.MIN_QUERY_LENGTH,
        max_length=config.MAX_QUERY_LENGTH,
        description="Search query",
    ),
    limit: int = Query(
        config.DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=config.MAX_SEARCH_RESULTS,
        description="Maximum number of results",
    ),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year: Optional[int] = Query(None, ge=1880, le=2030, description="Filter by year"),
    min_rating: Optional[float] = Query(
        None, ge=0, le=10, description="Minimum IMDB rating"
    ),
    max_rating: Optional[float] = Query(
        None, ge=0, le=10, description="Maximum IMDB rating"
    ),
    director: Optional[str] = Query(None, description="Filter by director"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    sort_by: str = Query(
        "rating",
        pattern="^(rating|year|title|duration|budget)$",
        description="Sort by field",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
):
    """Enhanced search for movies with comprehensive filtering and sorting"""
    start_time = time.time()

    # Create cache key
    cache_key = f"search:{q}:{limit}:{offset}:{genre}:{year}:{min_rating}:{max_rating}:{director}:{actor}:{sort_by}:{sort_order}"

    # Check cache first
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            execution_time = (time.time() - start_time) * 1000
            cached_result["execution_time_ms"] = execution_time
            cached_result["cached"] = True
            return SearchResponse(**cached_result)

    try:
        # Validate rating range
        if (
            min_rating is not None
            and max_rating is not None
            and min_rating > max_rating
        ):
            raise HTTPException(
                status_code=400, detail="min_rating cannot be greater than max_rating"
            )

        movies, total_count, filters_applied = search_movies_in_df(
            q,
            limit,
            offset,
            genre,
            year,
            min_rating,
            max_rating,
            director,
            actor,
            sort_by,
            sort_order,
        )

        execution_time = (time.time() - start_time) * 1000

        # Pagination info
        pagination = {
            "limit": limit,
            "offset": offset,
            "total": total_count,
            "has_next": offset + limit < total_count,
            "has_prev": offset > 0,
        }

        result = {
            "movies": movies,
            "total_count": total_count,
            "query": q,
            "filters": filters_applied,
            "execution_time_ms": execution_time,
            "cached": False,
            "pagination": pagination,
        }

        # Cache the result
        if cache:
            cache.set(cache_key, result)

        return SearchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=500, detail=config.ERROR_MESSAGES["search_failed"]
        )


@app.get(f"{config.API_PREFIX}/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(
    q: str = Query(
        ...,
        min_length=config.MIN_SUGGESTIONS_QUERY_LENGTH,
        max_length=config.MAX_SUGGESTIONS_QUERY_LENGTH,
        description="Query for suggestions",
    ),
    limit: int = Query(
        config.DEFAULT_SUGGESTIONS_LIMIT,
        ge=1,
        le=config.MAX_SUGGESTIONS,
        description="Maximum number of suggestions",
    ),
):
    """Get autocomplete suggestions for movie search with enhanced features"""
    start_time = time.time()

    # Check cache first
    cache_key = f"suggestions:{q}:{limit}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            execution_time = (time.time() - start_time) * 1000
            cached_result["execution_time_ms"] = execution_time
            cached_result["cached"] = True
            return SuggestionsResponse(**cached_result)

    try:
        suggestions = []
        total_available = 0

        if trie:
            # Use trie for suggestions
            all_suggestions = trie.printAutoSuggestions(q)
            if isinstance(all_suggestions, list):
                total_available = len(all_suggestions)
                suggestions = all_suggestions[:limit]
            else:
                # Handle special return codes (0 or -1)
                total_available = 0
                suggestions = []
        else:
            # Fallback: search in DataFrame
            if movies_df is not None:
                query_lower = q.lower()
                matching_titles = (
                    movies_df[
                        movies_df["movie_title"]
                        .str.lower()
                        .str.startswith(query_lower, na=False)
                    ]["movie_title"]
                    .dropna()
                    .unique()
                )
                suggestions = list(matching_titles)[:limit]
                total_available = len(matching_titles)

        execution_time = (time.time() - start_time) * 1000

        result = {
            "suggestions": suggestions,
            "query": q,
            "execution_time_ms": execution_time,
            "cached": False,
            "total_available": total_available,
        }

        # Cache the result
        if cache:
            cache.set(cache_key, result)

        return SuggestionsResponse(**result)

    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(
            status_code=500, detail=config.ERROR_MESSAGES["suggestions_failed"]
        )


@app.get(f"{config.API_PREFIX}/movies", response_model=List[MovieModel])
async def get_movies(
    limit: int = Query(20, ge=1, le=100, description="Number of movies to return"),
    offset: int = Query(0, ge=0, description="Number of movies to skip"),
    sort_by: str = Query(
        "rating",
        pattern="^(rating|year|title|duration|budget)$",
        description="Sort by field",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
):
    """Get paginated list of all movies with sorting"""
    try:
        if movies_df is None:
            return get_fallback_movies(limit)

        # Apply sorting
        sort_column_mapping = {
            "rating": "imdb_score",
            "year": "title_year",
            "title": "movie_title",
            "duration": "duration",
            "budget": "budget",
        }

        sorted_df = movies_df.copy()
        if sort_by in sort_column_mapping:
            sort_column = sort_column_mapping[sort_by]
            ascending = sort_order.lower() == "asc"
            sorted_df = sorted_df.sort_values(
                sort_column, ascending=ascending, na_position="last"
            )

        # Get paginated movies
        paginated_df = sorted_df.iloc[offset : offset + limit]

        movies = []
        for _, row in paginated_df.iterrows():
            try:
                movie_dict = movie_to_dict(row)
                movies.append(MovieModel(**movie_dict))
            except Exception as e:
                logger.warning(f"Failed to create movie model: {e}")
                continue

        return movies

    except Exception as e:
        logger.error(f"Get movies error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve movies")


@app.get(f"{config.API_PREFIX}/movies/{{movie_id}}", response_model=MovieModel)
async def get_movie_by_id(movie_id: int):
    """Get specific movie by ID/index"""
    try:
        if movies_df is None or movie_id >= len(movies_df) or movie_id < 0:
            raise HTTPException(
                status_code=404, detail=config.ERROR_MESSAGES["not_found"]
            )

        row = movies_df.iloc[movie_id]
        movie_dict = movie_to_dict(row)
        return MovieModel(**movie_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get movie by ID error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve movie")


@app.get(f"{config.API_PREFIX}/genres")
async def get_genres():
    """Get list of all available genres"""
    try:
        if movies_df is None:
            return {"genres": ["Action", "Drama", "Comedy", "Thriller", "Horror"]}

        # Extract all genres from the pipe-separated genre strings
        all_genres = set()
        for genres_str in movies_df["genres"].dropna():
            if isinstance(genres_str, str):
                genres = [g.strip() for g in genres_str.split("|") if g.strip()]
                all_genres.update(genres)

        return {"genres": sorted(list(all_genres))}

    except Exception as e:
        logger.error(f"Get genres error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve genres")


@app.get(f"{config.API_PREFIX}/directors")
async def get_directors(
    limit: int = Query(50, ge=1, le=200, description="Number of directors to return"),
    search: Optional[str] = Query(None, description="Search directors by name"),
):
    """Get list of directors with optional search"""
    try:
        if movies_df is None:
            return {
                "directors": [
                    "Christopher Nolan",
                    "Quentin Tarantino",
                    "Martin Scorsese",
                ]
            }

        directors_df = movies_df["director_name"].dropna().drop_duplicates()

        if search:
            directors_df = directors_df[
                directors_df.str.contains(search, case=False, na=False)
            ]

        directors = sorted(directors_df.head(limit).tolist())
        return {"directors": directors}

    except Exception as e:
        logger.error(f"Get directors error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve directors")


@app.get(f"{config.API_PREFIX}/stats", response_model=StatsResponse)
async def get_stats():
    """Get comprehensive database and system statistics"""
    try:
        if movies_df is None:
            database_stats = {"status": "Database not loaded"}
        else:
            # Database statistics
            database_stats = {
                "total_movies": len(movies_df),
                "unique_directors": movies_df["director_name"].nunique(),
                "unique_actors": movies_df["actor_1_name"].nunique(),
                "unique_genres": len(
                    set(
                        genre.strip()
                        for genres in movies_df["genres"].dropna()
                        for genre in genres.split("|")
                        if genre.strip()
                    )
                ),
                "year_range": {
                    "min": (
                        int(movies_df["title_year"].min())
                        if pd.notna(movies_df["title_year"].min())
                        else None
                    ),
                    "max": (
                        int(movies_df["title_year"].max())
                        if pd.notna(movies_df["title_year"].max())
                        else None
                    ),
                },
                "rating_range": {
                    "min": (
                        float(movies_df["imdb_score"].min())
                        if pd.notna(movies_df["imdb_score"].min())
                        else None
                    ),
                    "max": (
                        float(movies_df["imdb_score"].max())
                        if pd.notna(movies_df["imdb_score"].max())
                        else None
                    ),
                    "avg": (
                        float(movies_df["imdb_score"].mean())
                        if pd.notna(movies_df["imdb_score"].mean())
                        else None
                    ),
                },
                "duration_stats": {
                    "min": (
                        int(movies_df["duration"].min())
                        if pd.notna(movies_df["duration"].min())
                        else None
                    ),
                    "max": (
                        int(movies_df["duration"].max())
                        if pd.notna(movies_df["duration"].max())
                        else None
                    ),
                    "avg": (
                        float(movies_df["duration"].mean())
                        if pd.notna(movies_df["duration"].mean())
                        else None
                    ),
                },
            }

        # Performance statistics
        performance_stats = performance_monitor.get_performance_summary()

        # Cache statistics
        cache_stats = cache.get_stats() if cache else None

        # System statistics
        try:
            import psutil

            system_stats = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "percent": psutil.virtual_memory().percent,
                    "available_gb": round(
                        psutil.virtual_memory().available / (1024**3), 2
                    ),
                },
                "disk": {
                    "percent": (
                        psutil.disk_usage("/").percent
                        if os.name != "nt"
                        else psutil.disk_usage("C:\\").percent
                    ),
                    "free_gb": (
                        round(psutil.disk_usage("/").free / (1024**3), 2)
                        if os.name != "nt"
                        else round(psutil.disk_usage("C:\\").free / (1024**3), 2)
                    ),
                },
            }
        except ImportError:
            system_stats = {"status": "psutil not available"}

        return StatsResponse(
            database=database_stats,
            performance=performance_stats,
            cache=cache_stats,
            system=system_stats,
        )

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# Admin endpoints (only in debug mode)
if config.DEBUG:

    @app.post(f"{config.API_PREFIX}/admin/cache/clear")
    async def clear_cache():
        """Clear the application cache"""
        if cache:
            cache.clear()
            logger.info("Cache cleared by admin request")
            return {
                "message": "Cache cleared successfully",
                "timestamp": datetime.now().isoformat(),
            }
        return {"message": "Cache not enabled"}

    @app.get(f"{config.API_PREFIX}/admin/cache/stats")
    async def get_cache_stats():
        """Get detailed cache statistics"""
        if cache:
            return cache.get_stats()
        return {"message": "Cache not enabled"}

    @app.get(f"{config.API_PREFIX}/admin/performance")
    async def get_performance_metrics():
        """Get detailed performance metrics"""
        return {
            "performance": performance_monitor.get_performance_summary(),
            "health": performance_monitor.get_health_status(),
            "alerts": alert_manager.get_recent_alerts(),
        }

    @app.post(f"{config.API_PREFIX}/admin/reload")
    async def reload_data():
        """Reload movie data (development only)"""
        global movies_df, avl_tree, trie
        try:
            # Reload data
            movies_df = pd.read_csv(config.MOVIE_CSV_PATH, encoding=config.DB_ENCODING)

            # Reinitialize structures
            from trie import Trie
            from avl import AVLTree

            avl_tree = AVLTree()
            for title in movies_df["movie_title"].dropna():
                clean_title = title.strip()
                if clean_title:
                    avl_tree.insert(clean_title)

            trie = Trie()
            movie_titles = [
                title.strip()
                for title in movies_df["movie_title"].dropna()
                if title.strip()
            ]
            trie.formTrie(movie_titles)

            # Clear cache
            if cache:
                cache.clear()

            logger.info("Data reloaded successfully")
            return {
                "message": "Data reloaded successfully",
                "movies_loaded": len(movies_df),
            }

        except Exception as e:
            logger.error(f"Failed to reload data: {e}")
            raise HTTPException(status_code=500, detail="Failed to reload data")


# Static file serving for development
if config.DEBUG:
    app.mount("/static", StaticFiles(directory="static"), name="static")


# Health check endpoint for load balancers
@app.get("/health")
async def simple_health():
    """Simple health check for load balancers"""
    return {"status": "ok"}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL.lower(),
        workers=config.WORKER_COUNT if not config.RELOAD else 1,
    )
