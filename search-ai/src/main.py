# main.py - Cultural Recommendation Service
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import os
from dotenv import load_dotenv

from src.api import search_routes
from src.api.enhanced_search_routes import router as enhanced_search_router
from src.api.recommendation_routes import router as recommendation_router
from src.database.qdrant_client import init_qdrant, qdrant
from src.utils.logger import setup_logging, get_logger
from src.config.settings import settings

# Load .env if present (helps local dev)
load_dotenv()

# Initialize logging
logger = setup_logging(log_level=settings.LOG_LEVEL)

# Read internal API key from environment (same key backend will send)
AI_SERVICE_KEY = os.getenv("AI_SERVICE_KEY")  # e.g. "supersecretkey"
ENV = os.getenv("ENV", "development")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    startup_start = time.time()
    logger.info("Starting SearchAI Cultural Recommendation Service")

    try:
        # Initialize Qdrant
        init_qdrant()
        logger.info("Qdrant initialized successfully")

        # Verify connection
        collections = qdrant.get_collections()
        logger.info(f"Connected to Qdrant - Collections: {[c.name for c in collections.collections]}")

        startup_time = (time.time() - startup_start) * 1000
        logger.info(f"Service started successfully in {startup_time:.2f}ms")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

    # Shutdown
    logger.info("Shutting down SearchAI Service")


# Create FastAPI app
app = FastAPI(
    title="SearchAI - Cultural Recommendation Service",
    description="AI-powered cultural recommendation system for Indian artisan marketplace",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://localhost:4200",  # Angular default
        "http://localhost:8080",  # Vue default
        "*"  # Allow all for development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------
# Optional API-key middleware
# -----------------------
@app.middleware("http")
async def internal_key_middleware(request: Request, call_next):
    """
    Enforce internal API key for protected endpoints.
    - If AI_SERVICE_KEY is not set, enforcement is skipped (convenient for local dev).
    - If set, middleware expects header `x-api-key: <AI_SERVICE_KEY>` for protected routes.
    - Public endpoints (/, /health, /docs, /openapi.json) remain accessible without the key.
    """
    try:
        path = (request.url.path or "").lower()

        # Public endpoints that should remain accessible without the API key
        public_paths = ("/", "/health", "/docs", "/openapi.json", "/redoc")

        # Protected API prefixes (update these if your router prefixes change)
        protected_prefixes = (
            "/search",
            "/recommendation",
            "/enhanced_search",
            "/index",
            "/debug",
        )

        # If no key configured, skip enforcement (dev convenience)
        if AI_SERVICE_KEY:
            # If request targets a protected prefix, require the header
            if any(path.startswith(p) for p in protected_prefixes):
                provided = request.headers.get("x-api-key")
                if provided != AI_SERVICE_KEY:
                    client = request.client.host if request.client else "unknown"
                    logger.warning(
                        "Unauthorized request to %s from %s (missing/invalid x-api-key)",
                        path,
                        client,
                    )
                    raise HTTPException(status_code=401, detail="Unauthorized")

        # Lightweight request logging
        client_host = request.client.host if request.client else "unknown"
        logger.info("Request: %s %s from %s", request.method, path, client_host)

        response = await call_next(request)

        logger.info("Response: %s %s -> status %s", request.method, path, response.status_code)
        return response

    except HTTPException:
        # re-raise HTTPException so FastAPI handles it correctly
        raise
    except Exception as e:
        logger.exception("Unexpected error in middleware for path %s: %s", request.url.path, e)
        # Wrap unexpected errors into a 500 so client gets consistent response
        raise HTTPException(status_code=500, detail="Internal server error")


# Request logging middleware (keeps previous simple logging too)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
    return response


# Include routers
app.include_router(recommendation_router, tags=["Recommendations"])
app.include_router(search_routes.router, tags=["Search"])
app.include_router(enhanced_search_router, tags=["Enhanced Search"])


# Health check endpoint
@app.get("/health")
def health_check():
    """Service health check"""
    try:
        collections = qdrant.get_collections()
        return {
            "status": "healthy",
            "service": "SearchAI Cultural Recommendations",
            "database": "connected",
            "collections": [c.name for c in collections.collections]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Root endpoint
@app.get("/")
def root():
    """Service information"""
    return {
        "service": "SearchAI Cultural Recommendation Service",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "recommendations": "/recommendations/similar",
            "search": "/search",
            "health": "/health",
            "docs": "/docs"
        },
        "api_key_protected": bool(AI_SERVICE_KEY)
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting SearchAI application with uvicorn (dev)")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
