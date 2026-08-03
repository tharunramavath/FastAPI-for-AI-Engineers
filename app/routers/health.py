"""
routers/health.py — Health & Readiness Checks
===============================================
CONCEPT: Path Parameters + Public Endpoints

Health checks are:
  - PUBLIC (no auth) — so load balancers and Kubernetes can call them
  - Fast — they should return in < 50ms
  - Informative — tell you which models are loaded, current status

Why AI engineers need this:
  - Kubernetes uses /health to know if your pod is ready to serve traffic
  - Load balancers route to healthy instances only
  - On-call engineers hit /health first when investigating an incident

CONCEPT: Path Parameters
  /models/{model_name} — the {model_name} part is a path parameter
  FastAPI captures it and passes it to your function.
"""

from fastapi import APIRouter, HTTPException, status, Path
from app.schemas.response import HealthResponse, ModelInfo
from app.services.model_service import model_service, AVAILABLE_MODELS
from app.config import settings

router = APIRouter(tags=["Health & Models"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check — no auth required",
)
async def health_check():
    """
    Returns the current health of the API.
    No API key required — load balancers need to call this.
    """
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        models_loaded=model_service.loaded_models,
        uptime_seconds=round(model_service.get_uptime(), 1),
    )


@router.get(
    "/models/{model_name}",
    response_model=ModelInfo,
    summary="Get details for a specific model",
)
async def get_model(
    model_name: str = Path(
        ...,
        description="Name of the model",
        examples=["sentiment", "summarizer", "llm"],
    ),
):
    """
    CONCEPT: Path Parameters

    {model_name} in the route → `model_name: str` in the function.
    FastAPI extracts the value from the URL automatically.

    Example: GET /models/sentiment → model_name = "sentiment"

    Path() lets you add validation and documentation.
    """
    if model_name not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found. Available: {list(AVAILABLE_MODELS.keys())}",
        )

    return AVAILABLE_MODELS[model_name]
