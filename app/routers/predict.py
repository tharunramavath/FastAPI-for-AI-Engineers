"""
routers/predict.py — Core Inference Endpoint
==============================================
CONCEPTS COVERED:
  - APIRouter (organizing routes into modules)
  - POST endpoint with request body
  - Dependency Injection with Depends()
  - Background Tasks (fire-and-forget after response)
  - Response Model (shapes the JSON output)
  - HTTP Status Codes
  - Query Parameters (optional filters on a GET endpoint)

This is the most important file — the pattern here repeats
across every AI inference API in production.
"""

import logging
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from app.schemas.request import PredictRequest
from app.schemas.response import PredictResponse, ModelsResponse
from app.middleware.auth import verify_api_key
from app.services.model_service import model_service

logger = logging.getLogger(__name__)

# APIRouter groups related endpoints together.
# The prefix "/predict" means all routes here are at /predict/...
# But we'll keep this router's routes flat — the router is included
# in main.py which assigns the prefix.
router = APIRouter(tags=["Inference"])


# ─────────────────────────────────────────────────────────
# Background task — runs AFTER the response is sent to the client.
# The client gets their answer immediately; we log/bill/analyze after.
# ─────────────────────────────────────────────────────────
def log_inference(request_id: str, model: str, tokens: int):
    """
    Simulates post-inference logging (metrics, billing, audit log).

    In production: write to a database, send to a metrics service,
    update token usage counters, etc.

    This runs in the background — the client doesn't wait for this.
    """
    logger.info(f"[background] request_id={request_id} model={model} tokens={tokens}")
    # In reality: db.insert(InferenceLog(request_id=..., model=..., tokens=...))


# ─────────────────────────────────────────────────────────
# CORE ENDPOINT: POST /predict
# ─────────────────────────────────────────────────────────
@router.post(
    "/predict",
    response_model=PredictResponse,            # FastAPI validates & serializes output
    status_code=200,
    summary="Run model inference",
    description="Send text to a model and get a prediction back synchronously.",
)
async def predict(
    body: PredictRequest,                      # ← JSON body, validated by Pydantic
    background_tasks: BackgroundTasks,         # ← FastAPI injects this automatically
    _: str = Depends(verify_api_key),          # ← Auth gate; _ = we don't use the key value
):
    """
    CONCEPT: How a POST endpoint works in FastAPI

    1. Client sends POST /predict with JSON body
    2. FastAPI deserializes JSON → PredictRequest (validates it)
    3. verify_api_key() runs (via Depends) — 401 if invalid
    4. This function runs
    5. We call the model service
    6. FastAPI serializes PredictResponse → JSON and sends it back
    7. THEN background_tasks run (logging, billing, etc.)

    The underscore (_) in `_: str = Depends(verify_api_key)` means:
      "run the dependency for its side effects (auth), but I don't
       need the return value"
    """
    # Call the model service (async — doesn't block other requests)
    result = await model_service.predict(
        text=body.text,
        model_name=body.model,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        system_prompt=body.system_prompt,
    )

    # Register a background task — runs after response is sent
    # The client won't wait for this to finish
    background_tasks.add_task(
        log_inference,
        request_id=result.request_id,
        model=result.model,
        tokens=result.tokens_used,
    )

    return result  # FastAPI serializes this using PredictResponse


# ─────────────────────────────────────────────────────────
# GET /models — List available models
# CONCEPT: Query Parameters
# ─────────────────────────────────────────────────────────
@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List available models",
)
async def list_models(
    _: str = Depends(verify_api_key),
    available_only: bool = Query(
        default=True,
        description="If true, only return models that are currently available"
    ),
):
    """
    CONCEPT: Query Parameters

    Query params appear after the ? in the URL:
      GET /models?available_only=false

    FastAPI reads them from the function signature automatically.
    They're optional by default (if you give them a default value).

    Path params look like: /models/{model_name}  → def get_model(model_name: str)
    Query params look like: /models?x=1           → def list_models(x: int = 1)
    """
    all_models = model_service.get_available_models()

    if available_only:
        all_models = [m for m in all_models if m.is_available]

    return ModelsResponse(models=all_models, total=len(all_models))
