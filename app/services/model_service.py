"""
services/model_service.py — The Model Layer
=============================================
CONCEPT: Service Layer + Async/Await

This is where your actual ML model code lives.
It's separated from the router so:
  - Routers handle HTTP concerns (params, headers, status codes)
  - Services handle business logic (model loading, inference, processing)

CONCEPT: async def vs def
  - Use `async def` when your function does I/O (network calls, file reads,
    calling an external API like OpenAI)
  - Use `def` for pure CPU computation (actually running a local model)
  - FastAPI runs sync functions in a thread pool automatically — don't worry
    about blocking if your model is CPU-only

In a real app, this file would:
  - Load your model from disk at startup
  - Call model.predict() / pipeline() / openai.chat.completions.create()
  - Handle batching, caching, GPU memory

Here, everything is MOCKED with realistic delays to teach the patterns
without requiring a GPU or real model weights.
"""

import asyncio
import random
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator

from app.schemas.response import PredictResponse, ModelInfo


# ─────────────────────────────────────────────
# Simulated "loaded models" — in reality, these
# would be your actual model objects
# ─────────────────────────────────────────────
AVAILABLE_MODELS = {
    "sentiment": ModelInfo(
        name="sentiment",
        version="1.2.0",
        description="Classifies text as positive, negative, or neutral",
        input_type="text",
        max_tokens=50,
        is_available=True,
    ),
    "summarizer": ModelInfo(
        name="summarizer",
        version="2.0.1",
        description="Produces an abstractive summary of long text",
        input_type="text",
        max_tokens=512,
        is_available=True,
    ),
    "llm": ModelInfo(
        name="llm",
        version="3.1.0",
        description="General-purpose language model for text generation",
        input_type="text",
        max_tokens=2048,
        is_available=True,
    ),
}


class ModelService:
    """
    Encapsulates all model inference logic.

    In a production app:
      - __init__ loads models from disk / downloads weights
      - Each method calls the appropriate model
      - You'd inject this via FastAPI's dependency system
    """

    def __init__(self):
        # Track when the service started (for health checks)
        self.start_time = time.time()
        self.loaded_models = list(AVAILABLE_MODELS.keys())
        print("✅ ModelService initialized — models loaded")

    async def predict(
        self,
        text: str,
        model_name: str,
        max_tokens: int,
        temperature: float,
        system_prompt: str | None = None,
    ) -> PredictResponse:
        """
        Run inference and return a structured response.

        CONCEPT: async def
        We use async here because in a real app this would be:
          - An HTTP call to OpenAI / Anthropic API  →  I/O bound → use async
          - A call to a model server (TorchServe, Triton)  →  I/O bound → use async

        If you're running a local model synchronously (e.g., model.predict()),
        wrap it: result = await asyncio.to_thread(model.predict, text)
        """
        start = time.time()

        # Simulate model inference latency
        await asyncio.sleep(random.uniform(0.1, 0.4))

        # Mock outputs per model type
        output = self._mock_output(model_name, text, temperature)
        tokens_used = len(output.split()) + len(text.split())  # rough estimate

        latency_ms = (time.time() - start) * 1000

        return PredictResponse(
            request_id=str(uuid.uuid4()),
            model=model_name,
            output=output,
            confidence=round(random.uniform(0.75, 0.99), 3) if model_name == "sentiment" else None,
            tokens_used=tokens_used,
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.utcnow(),
        )

    async def stream_tokens(
        self,
        text: str,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        """
        CONCEPT: Async Generators for Streaming

        Instead of returning everything at once, we `yield` one token at a time.
        FastAPI's StreamingResponse wraps this generator.

        This is EXACTLY how OpenAI / Anthropic streaming works under the hood —
        Server-Sent Events (SSE) with tokens arriving one by one.

        AsyncGenerator[str, None]:
          - str  = the type of each yielded value
          - None = the return type (generators return nothing)
        """
        # Generate a fake response word by word
        fake_response = (
            f"Based on your input about '{text[:30]}...', "
            "here is a detailed response from the language model. "
            "Machine learning involves training models on large datasets "
            "to recognize patterns and make predictions. "
            "Deep learning uses neural networks with many layers "
            "to learn complex representations of data."
        )

        words = fake_response.split()
        for i, word in enumerate(words[:max_tokens]):
            # Yield one token (word) at a time
            yield word + " "
            # Simulate the delay between tokens (like a real LLM)
            await asyncio.sleep(0.05)

        # Signal end of stream
        yield "[DONE]"

    def get_available_models(self) -> list[ModelInfo]:
        return list(AVAILABLE_MODELS.values())

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def _mock_output(self, model_name: str, text: str, temperature: float) -> str:
        """Generate realistic-looking mock outputs per model."""
        if model_name == "sentiment":
            sentiments = ["POSITIVE (score: 0.94)", "NEGATIVE (score: 0.87)", "NEUTRAL (score: 0.71)"]
            return random.choice(sentiments)

        elif model_name == "summarizer":
            return f"Summary: The text discusses topics related to '{text[:40]}' with key themes around the subject matter presented."

        elif model_name == "llm":
            return (
                f"Response to '{text[:30]}...': This is a generated response from the language model. "
                f"Temperature was set to {temperature}, which affects the creativity of this output."
            )

        return "Unknown model output"


# ─────────────────────────────────────────────
# Module-level instance — loaded once at startup
# Routers import this and use it directly, OR
# you inject it via FastAPI's Depends() system
# ─────────────────────────────────────────────
model_service = ModelService()
