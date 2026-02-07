# """
# src/main.py

# Updated FastAPI entrypoint for the Vision AI microservice.

# Changes in this version:
# - Loads environment variables (via python-dotenv).
# - Adds an optional internal API-key enforcement middleware that checks `x-api-key`
#   on incoming requests to protected routes (applies to /vision/* by default).
# - Adds lightweight request logging for observability.
# - Keeps CORS and router registration as before.

# Run locally:
#     uvicorn src.main:app --host 0.0.0.0 --port 5001 --reload

# Important:
# - Set AI_SERVICE_KEY in the microservice environment to enable enforcement:
#     AI_SERVICE_KEY=supersecretkey
#   If AI_SERVICE_KEY is not set, middleware will skip enforcement (useful for dev).
# """

# import os
# import logging
# from dotenv import load_dotenv

# from fastapi import FastAPI, Request, HTTPException
# from fastapi.middleware.cors import CORSMiddleware

# # Import your router (ensure PYTHONPATH includes project root or run from project root)
# from .vision_ai.routes.vision_routes import router as vision_router
# # -----------------------
# # Environment & Logging
# # -----------------------
# load_dotenv()  # loads .env if present
# AI_SERVICE_KEY = os.getenv("AI_SERVICE_KEY")  # internal key used by backend
# ENV = os.getenv("ENV", "development")

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("vision_ai.main")


# # -----------------------
# # FastAPI app init
# # -----------------------
# app = FastAPI(
#     title="Vision AI Microservice",
#     description="AI-powered vision endpoints (story, similarity, pricing, fraud, etc.)",
#     version="1.0.0",
# )

# # CORS - open in dev; tighten in production
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # -----------------------
# # Optional API-key middleware
# # -----------------------
# @app.middleware("http")
# async def internal_key_middleware(request: Request, call_next):
#     """
#     Enforce internal API key for calls to /vision/* endpoints.
#     - If AI_SERVICE_KEY is not set, enforcement is skipped (convenient for local dev).
#     - If set, middleware expects header `x-api-key: <AI_SERVICE_KEY>` for protected routes.
#     - Health check, docs, and OpenAPI should remain accessible without the header.
#     """
#     try:
#         path = request.url.path or ""
#         # Only protect service API routes (change prefix if needed)
#         protect_prefix = "/vision"

#         if AI_SERVICE_KEY and path.startswith(protect_prefix):
#             provided = request.headers.get("x-api-key")
#             if provided != AI_SERVICE_KEY:
#                 # Log limited info (do NOT log keys)
#                 client = request.client.host if request.client else "unknown"
#                 logger.warning("Unauthorized request to %s from %s (missing/invalid x-api-key)", path, client)
#                 raise HTTPException(status_code=401, detail="Unauthorized")

#         # lightweight request logging
#         logger.info("Request: %s %s from %s", request.method, path, request.client.host if request.client else "unknown")
#         response = await call_next(request)
#         logger.info("Response: %s %s -> status %s", request.method, path, response.status_code)
#         return response

#     except HTTPException:
#         # re-raise HTTPException so FastAPI handles it correctly
#         raise
#     except Exception as e:
#         logger.exception("Unexpected error in middleware for path %s: %s", request.url.path, e)
#         # Wrap unexpected errors into a 500 so client gets consistent response
#         raise HTTPException(status_code=500, detail="Internal server error")


# # -----------------------
# # Register routers & health
# # -----------------------
# app.include_router(vision_router, prefix="/vision", tags=["Vision AI"])


# @app.get("/")
# def health_check():
#     """Lightweight health-check / landing endpoint."""
#     return {"status": "Vision AI microservice is running", "env": ENV, "protected": bool(AI_SERVICE_KEY)}


# # -----------------------
# # Startup/shutdown events (optional)
# # -----------------------
# @app.on_event("startup")
# async def startup_event():
#     # Log startup config without printing secrets
#     logger.info("Starting Vision AI microservice (env=%s). API key enforcement: %s", ENV, bool(AI_SERVICE_KEY))


# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("Shutting down Vision AI microservice")



"""
Updated FastAPI entrypoint for the Vision AI microservice with improved timeout handling.
Uses modern lifespan events instead of deprecated on_event.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from .vision_ai.routes.vision_routes import router as vision_router

# Load environment
load_dotenv()
AI_SERVICE_KEY = os.getenv("AI_SERVICE_KEY")
ENV = os.getenv("ENV", "production")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vision_ai.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown")
    """
    # Startup
    logger.info("Starting Vision AI microservice (env=%s). API key enforcement: %s", 
               ENV, bool(AI_SERVICE_KEY))
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Vision AI microservice")


# FastAPI app with lifespan
app = FastAPI(
    title="Vision AI Microservice",
    description="AI-powered vision endpoints",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add timeout to all requests"""
    try:
        # Set timeout for AI processing requests
        timeout = 300 if request.url.path.startswith("/vision") else 30
        
        response = await asyncio.wait_for(
            call_next(request),
            timeout=timeout
        )
        return response
        
    except asyncio.TimeoutError:
        logger.error(f"Request timeout for {request.url.path}")
        raise HTTPException(
            status_code=504,
            detail="Request timeout - AI processing took too long"
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def internal_key_middleware(request: Request, call_next):
    """Optional API key enforcement"""
    try:
        path = request.url.path or ""
        protect_prefix = "/vision"

        if AI_SERVICE_KEY and path.startswith(protect_prefix):
            provided = request.headers.get("x-api-key")
            if provided != AI_SERVICE_KEY:
                client = request.client.host if request.client else "unknown"
                logger.warning("Unauthorized request to %s from %s", path, client)
                raise HTTPException(status_code=401, detail="Unauthorized")

        logger.info("Request: %s %s from %s", 
                   request.method, path, 
                   request.client.host if request.client else "unknown")
        
        response = await call_next(request)
        
        logger.info("Response: %s %s -> status %s", 
                   request.method, path, response.status_code)
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in middleware: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

# Register routers
app.include_router(vision_router, prefix="/vision", tags=["Vision AI"])

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "Vision AI microservice is running",
        "env": ENV,
        "protected": bool(AI_SERVICE_KEY),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
def detailed_health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "vision-ai",
        "version": "1.0.0",
        "env": ENV,
        "timestamp": datetime.utcnow().isoformat()
    }