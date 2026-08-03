"""
routers/stream.py — Token Streaming (SSE)
==========================================
CONCEPT: StreamingResponse + Async Generators

This is how ChatGPT-style streaming works:
  - Server sends tokens one at a time as they're generated
  - Client sees words appearing progressively
  - Uses Server-Sent Events (SSE) format: `data: <token>\n\n`

Why AI engineers MUST know this:
  - LLM latency is high — users shouldn't stare at a blank screen
  - Streaming makes UIs feel responsive
  - OpenAI, Anthropic, Gemini all stream this way
  - You'll implement this for any LLM-powered product

How it works:
  1. Client makes a POST request (just like /predict)
  2. Server responds with Content-Type: text/event-stream
  3. The connection stays open
  4. Server sends data in chunks: "data: hello \n\n"
  5. Client reads chunks as they arrive
  6. Server sends "data: [DONE]\n\n" to signal end
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.schemas.request import StreamRequest
from app.middleware.auth import verify_api_key
from app.services.model_service import model_service

router = APIRouter(tags=["Streaming"])


async def token_generator(text: str, max_tokens: int):
    """
    CONCEPT: Async Generator

    An async generator is like a regular generator (uses `yield`)
    but it can also `await` things between yields.

    FastAPI's StreamingResponse wraps this generator and sends
    each yielded string as a chunk to the client.

    The `data: ...\n\n` format is the Server-Sent Events (SSE) spec.
    Each event must end with TWO newlines.
    """
    async for token in model_service.stream_tokens(text, max_tokens):
        if token == "[DONE]":
            # Signal end of stream in SSE format
            yield "data: [DONE]\n\n"
        else:
            # Each token is sent as an SSE event
            yield f"data: {token}\n\n"


@router.post(
    "/stream",
    summary="Stream model output token by token",
    description="Returns a Server-Sent Events (SSE) stream. Connect with EventSource or curl -N.",
    response_description="A stream of SSE events, each containing one token.",
)
async def stream_predict(
    body: StreamRequest,
    _: str = Depends(verify_api_key),
):
    """
    CONCEPT: StreamingResponse

    Instead of returning a dict/Pydantic model, we return a
    StreamingResponse that wraps an async generator.

    Key parameters:
      - content: the async generator that yields chunks
      - media_type: "text/event-stream" is the SSE content type

    Test this with:
      curl -N -X POST http://localhost:8000/stream \\
        -H "X-API-Key: test-key-123" \\
        -H "Content-Type: application/json" \\
        -d '{"text": "Explain neural networks"}'

    The -N flag disables curl's output buffering so you see tokens
    arriving one by one.
    """
    return StreamingResponse(
        content=token_generator(body.text, body.max_tokens),
        media_type="text/event-stream",
        headers={
            # These headers prevent proxies/browsers from buffering the stream
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
