"""
schemas/response.py — Output Structures
=========================================
CONCEPT: Response Models

Define what your API *returns*. FastAPI uses these to:
  1. Serialize your Python objects to JSON automatically
  2. Filter out fields you don't want to expose (e.g., internal IDs)
  3. Document the response shape in /docs

Why AI engineers need this:
  - Consistent output format across all model endpoints
  - OpenAI, Anthropic, Hugging Face all return structured JSON — you should too
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PredictResponse(BaseModel):
    """Standard response from the /predict endpoint."""

    request_id: str = Field(description="Unique ID for this inference call")
    model: str = Field(description="Which model was used")
    output: str = Field(description="The model's output text")
    confidence: Optional[float] = Field(
        default=None,
        description="Confidence score (0.0 to 1.0), if available"
    )
    tokens_used: int = Field(description="Number of tokens consumed")
    latency_ms: float = Field(description="Inference time in milliseconds")
    timestamp: datetime = Field(description="When this request was processed")


class ModelInfo(BaseModel):
    """Metadata about a single model."""

    name: str
    version: str
    description: str
    input_type: str           # "text", "image", "audio"
    max_tokens: int
    is_available: bool


class ModelsResponse(BaseModel):
    """Response from the /models endpoint."""

    models: List[ModelInfo]
    total: int


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str               # "ok" or "degraded"
    environment: str
    models_loaded: List[str]
    uptime_seconds: float


class ErrorResponse(BaseModel):
    """Standard error shape — returned on 4xx and 5xx errors."""

    error: str                # Human-readable error message
    detail: Optional[str] = None   # Optional extra detail
    request_id: Optional[str] = None


class VisionResponse(BaseModel):
    """Response from the /vision/analyze endpoint."""

    request_id: str
    filename: str
    file_size_bytes: int
    detected_objects: List[str]
    caption: str
    latency_ms: float
