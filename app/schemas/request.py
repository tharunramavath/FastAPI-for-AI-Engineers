"""
schemas/request.py — Input Validation
=======================================
CONCEPT: Pydantic Models for Request Bodies

This is where you define WHAT your API accepts.
FastAPI reads this and automatically:
  1. Validates the incoming JSON
  2. Shows it in the /docs UI
  3. Returns a clear 422 error if validation fails

Why AI engineers need this:
  - LLM APIs need strict input validation (max_tokens, temperature ranges)
  - Prevents garbage inputs from reaching your expensive model
  - Self-documenting — teammates see exactly what the API expects
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from app.config import settings


class PredictRequest(BaseModel):
    """Request body for the /predict endpoint."""

    text: str = Field(
        ...,                          # "..." means required (no default)
        min_length=1,
        max_length=settings.max_input_length,
        description="The input text to run through the model",
        examples=["I absolutely love this product!"]
    )

    model: Literal["sentiment", "summarizer", "llm"] = Field(
        default="sentiment",
        description="Which model to use for inference"
    )

    max_tokens: int = Field(
        default=100,
        ge=1,       # ge = greater than or equal
        le=2048,    # le = less than or equal
        description="Maximum tokens in the model output"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0=deterministic, 2=creative)"
    )

    # Optional field — not required in the request
    system_prompt: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional system instruction for LLM models"
    )

    # Custom validator — runs AFTER pydantic's built-in validation
    @field_validator("text")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Trim leading/trailing whitespace from input text."""
        return v.strip()

    # Pydantic v2 config
    model_config = {
        # This generates example JSON in the /docs UI
        "json_schema_extra": {
            "examples": [
                {
                    "text": "I love this product, it changed my life!",
                    "model": "sentiment",
                    "max_tokens": 50,
                    "temperature": 0.0
                }
            ]
        }
    }


class StreamRequest(BaseModel):
    """Request body for the /stream endpoint (token-by-token output)."""

    text: str = Field(..., min_length=1, max_length=settings.max_input_length)
    model: Literal["llm"] = Field(default="llm")
    max_tokens: int = Field(default=200, ge=1, le=2048)
