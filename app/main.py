"""
app/main.py — Application Entry Point
=======================================
CONCEPTS COVERED:
  - FastAPI app creation
  - Lifespan events (startup / shutdown)
  - Registering middleware
  - Including routers
  - Global exception handlers
  - CORS (Cross-Origin Resource Sharing)

This is the "glue" file that wires everything together.
It's the file you pass to uvicorn:
  uvicorn app.main:app --reload
         ^^^^^^^^ ^^^
         module   FastAPI instance name
"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# On Windows, the console often uses cp1252 which can't print emoji (✅, 🚀).
# Force UTF-8 output so the startup logs work out of the box.
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import settings
from app.middleware.logging_mw import LoggingMiddleware
from app.routers import predict, stream, vision, health


# ─────────────────────────────────────────────────────────
# CONCEPT: Lifespan Events (startup / shutdown)
#
# The @asynccontextmanager pattern replaces the old @app.on_event("startup").
# Code BEFORE yield runs at startup (load models, connect to DB).
# Code AFTER yield runs at shutdown (cleanup, close connections).
#
# Why AI engineers need this:
#   - Loading an ML model takes 5–30 seconds
#   - You want to load it ONCE at startup, not on every request
#   - At shutdown, you flush logs, close GPU memory, etc.
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────
    print("🚀 Starting AI Model Serving API...")
    print(f"   Environment: {settings.environment}")
    print(f"   Docs available at: http://localhost:8000/docs")

    # In a real app:
    #   model = load_model("/models/llm-7b")        # slow, but only once
    #   app.state.model = model                     # store on app.state
    #   db = await create_db_connection()
    #   app.state.db = db

    print("✅ Startup complete — ready to serve requests")

    yield  # ← app is running while we're here

    # ── SHUTDOWN ─────────────────────────────────────────
    print("🛑 Shutting down...")
    # In a real app: await db.close(), model.unload(), flush_logs()
    print("👋 Shutdown complete")


# ─────────────────────────────────────────────────────────
# Create the FastAPI application
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="""
## AI Model Serving API

A production-style API for serving ML models.

### Authentication
All endpoints (except /health) require an `X-API-Key` header.

### Available Models
- **sentiment** — text classification (positive/negative/neutral)
- **summarizer** — abstractive text summarization
- **llm** — general-purpose text generation with streaming support

### Quick Start
1. Hit `/health` to verify the API is running
2. Set `X-API-Key: test-key-123` in your headers
3. POST to `/predict` with a JSON body
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
)


# ─────────────────────────────────────────────────────────
# CONCEPT: Middleware Registration
#
# Middleware is added with app.add_middleware().
# Order matters: middleware added LAST runs FIRST (like a stack).
#
# CORS middleware: required if your frontend is on a different domain.
# In production, replace "*" with your actual frontend URL.
# ─────────────────────────────────────────────────────────
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod: ["https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────
# CONCEPT: Global Exception Handlers
#
# Instead of try/except in every route, register handlers here.
# These catch unhandled exceptions and return proper JSON errors.
#
# Best practice: always return JSON errors (not HTML error pages)
# from an API — your clients are code, not humans.
# ─────────────────────────────────────────────────────────
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Catches ValueErrors raised anywhere in the app."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid input", "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catches any unhandled exception — last resort."""
    # In production: log to Sentry / Datadog here
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": "Something went wrong"},
    )


# ─────────────────────────────────────────────────────────
# CONCEPT: Including Routers
#
# Instead of defining all routes in main.py, we split them
# into router modules and include them here.
#
# The prefix= argument prepends to all routes in that router.
# Tags= groups them in the /docs UI.
# ─────────────────────────────────────────────────────────
app.include_router(health.router)  # /health, /models/{name} — no prefix, public
app.include_router(predict.router)  # /predict, /models
app.include_router(stream.router)  # /stream
app.include_router(vision.router)  # /vision/analyze


# ─────────────────────────────────────────────────────────
# Root endpoint — just a welcome message
# ─────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }
